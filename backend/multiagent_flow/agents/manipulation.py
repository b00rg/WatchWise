"""
Child Consumer Psychology Analyst — scores the `manipulation` radar axis.
Detects dark patterns that exploit children's psychological vulnerabilities.
"""
import json
from multiagent_flow.client import async_client, MODEL, parse_score
from multiagent_flow.age_bands import age_bracket_label

AGENT_ID = "manipulation"
AGENT_LABEL = "Child Consumer Psychology Analyst"

SYSTEM = """\
You are a Child Consumer Psychology Analyst who researches how digital media exploits \
children's developmental vulnerabilities for engagement and commercial gain. You have deep \
expertise in the specific manipulation tactics used in children's content: parasocial bonding, \
engineered FOMO, fake urgency, clickbait framing, and engagement-bait language that targets \
children who lack the cognitive defenses adults have.

You have been given a video transcript watched by a child. Use your tool to systematically \
scan for manipulation patterns, then write 2–3 sentences from your analytical perspective on \
what you find and what it means for a child viewer.

End your response on a new line with exactly:
SCORE: <0-100>
(0 = no manipulative tactics detected  |  100 = heavily engineered to exploit child psychology)\
"""

TOOLS = [
    {
        "name": "scan_manipulation_patterns",
        "description": (
            "Scan a transcript for dark patterns targeting children: parasocial manipulation, "
            "fake urgency, clickbait framing, FOMO triggers, and engagement bait. "
            "Returns categorised findings and a concern level."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "transcript": {"type": "string", "description": "The video transcript to scan"},
            },
            "required": ["transcript"],
        },
    }
]


def _scan_manipulation_patterns(transcript: str) -> dict:
    lower = transcript.lower()

    pattern_library = {
        "parasocial_bonding": [
            "i love you guys", "you're my favorite", "we're best friends",
            "our family", "you guys are everything", "i need you",
        ],
        "fake_urgency": [
            "right now", "don't miss", "limited time", "hurry", "last chance",
            "before it's gone", "act fast", "only today",
        ],
        "engagement_bait": [
            "smash that like", "hit subscribe", "ring the bell", "comment below",
            "let me know", "drop a like", "turn on notifications",
        ],
        "fomo_triggers": [
            "everyone is", "you don't want to miss", "viral", "trending",
            "all your friends", "can you believe", "you've never seen",
        ],
        "clickbait_framing": [
            "you won't believe", "gone wrong", "exposed", "shocking", "secret",
            "they don't want you to know", "this is why", "wait for it",
        ],
    }

    found: dict[str, list] = {}
    for category, phrases in pattern_library.items():
        hits = [p for p in phrases if p in lower]
        if hits:
            found[category] = hits

    return {
        "patterns_detected": found,
        "categories_flagged": len(found),
        "high_concern": len(found) >= 3,
        "analyst_note": (
            f"{len(found)} manipulation categories detected. "
            + (
                "Content employs multiple overlapping tactics consistent with engagement-maximising "
                "design that exploits children's underdeveloped impulse control and parasocial tendencies."
                if len(found) >= 3 else
                "Some tactics present but not a coordinated manipulation pattern."
                if len(found) > 0 else
                "No explicit manipulation language detected in transcript."
            )
        ),
    }


def _handle_tool(name: str, inp: dict) -> dict:
    if name == "scan_manipulation_patterns":
        return _scan_manipulation_patterns(inp["transcript"])
    return {"error": f"Unknown tool: {name}"}


async def manipulation_agent(transcript: str, channel: str, age: int):
    bracket = age_bracket_label(age)

    user = (
        f"Child age: {age} (bracket: {bracket})\n"
        f"Channel: {channel}\n"
        f"Transcript (first 1500 chars):\n{transcript[:1500]}\n\n"
        "Identify any manipulation tactics targeting this child viewer."
    )

    yield {"type": "agent_start", "agent": AGENT_ID, "label": AGENT_LABEL}

    messages = [{"role": "user", "content": user}]
    for _ in range(3):
        full_text = ""
        async with async_client.messages.stream(
            model=MODEL, max_tokens=400, system=SYSTEM,
            messages=messages, tools=TOOLS,
        ) as stream:
            async for text in stream.text_stream:
                full_text += text
                yield {"type": "token", "agent": AGENT_ID, "text": text}
            final_msg = await stream.get_final_message()

        if final_msg.stop_reason == "tool_use":
            tool_results = []
            for block in final_msg.content:
                if block.type == "tool_use":
                    result = _handle_tool(block.name, block.input)
                    yield {"type": "tool_call", "agent": AGENT_ID, "tool": block.name}
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": json.dumps(result),
                    })
            messages.append({"role": "assistant", "content": final_msg.content})
            messages.append({"role": "user", "content": tool_results})
        else:
            yield {"type": "agent_done", "agent": AGENT_ID, "label": AGENT_LABEL, "score": parse_score(full_text)}
            return

    yield {"type": "agent_done", "agent": AGENT_ID, "label": AGENT_LABEL, "score": 50}
