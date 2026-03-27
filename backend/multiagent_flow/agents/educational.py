"""
Child Development & Learning Specialist — scores the `educational_deficit` radar axis.
Higher score = more lacking in educational value (consistent "bad = high" direction as other axes).
"""
import json
from multiagent_flow.client import async_client, MODEL, parse_score
from multiagent_flow.age_bands import age_bracket_label

AGENT_ID = "educational_deficit"
AGENT_LABEL = "Child Development & Learning Specialist"

SYSTEM = """\
You are a Child Development & Learning Specialist with a background in developmental psychology \
and curriculum design. You assess whether media content actively supports children's cognitive \
growth — through narrative structure, cause-and-effect reasoning, vocabulary building, and \
genuine curiosity — or whether it delivers empty stimulation with no transferable learning.

You have been given a video transcript watched by a child. Use your tool to run a structural \
quality analysis, then write 2–3 sentences from your developmental perspective on what this \
content offers (or fails to offer) a child's developing mind.

End your response on a new line with exactly:
SCORE: <0-100>
(0 = rich, age-appropriate educational content  |  100 = zero learning value, pure cognitive junk food)\
"""

TOOLS = [
    {
        "name": "analyze_transcript_quality",
        "description": (
            "Analyze a transcript for structural educational indicators: vocabulary complexity, "
            "presence of causal reasoning, question-asking, factual content signals, and hype language."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "transcript": {"type": "string", "description": "The video transcript to analyze"},
            },
            "required": ["transcript"],
        },
    }
]


def _analyze_transcript_quality(transcript: str) -> dict:
    words = transcript.lower().split()
    word_count = len(words)
    if word_count == 0:
        return {"error": "Empty transcript — no language to assess."}

    questions = transcript.count("?")
    exclamations = transcript.count("!")

    long_words = [w for w in words if len(w) > 8]
    vocab_complexity = round(len(long_words) / word_count, 3)

    hype = ["omg", "crazy", "insane", "literally", "epic", "amazing", "wow", "unbelievable", "shocking"]
    hype_count = sum(1 for w in words if w in hype)

    edu_signals = ["because", "therefore", "however", "explains", "causes", "results",
                   "scientists", "research", "discovered", "experiment", "hypothesis", "evidence"]
    edu_count = sum(1 for w in words if w in edu_signals)

    return {
        "word_count": word_count,
        "questions_asked": questions,
        "exclamations": exclamations,
        "exclamation_to_question_ratio": round(exclamations / max(questions, 1), 2),
        "vocabulary_complexity_ratio": vocab_complexity,
        "hype_language_instances": hype_count,
        "educational_signal_words": edu_count,
        "structural_note": (
            "High exclamation-to-question ratio with low educational signal words suggests "
            "content prioritises emotional arousal over learning." if exclamations > questions * 2
            else "Language structure shows some balance between engagement and information."
        ),
    }


def _handle_tool(name: str, inp: dict) -> dict:
    if name == "analyze_transcript_quality":
        return _analyze_transcript_quality(inp["transcript"])
    return {"error": f"Unknown tool: {name}"}


async def educational_agent(transcript: str, channel: str, age: int):
    bracket = age_bracket_label(age)

    user = (
        f"Child age: {age} (bracket: {bracket})\n"
        f"Channel: {channel}\n"
        f"Transcript (first 1500 chars):\n{transcript[:1500]}\n\n"
        "Assess the educational quality of this content for a child of this age."
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
