"""
Cognitive Load Researcher — scores the `pacing` radar axis.
Uses the Fernando FSM string density model to quantify attentional demand.
"""
import json
from multiagent_flow.client import async_client, MODEL, parse_score
from multiagent_flow.age_bands import get_age_band, age_bracket_label

AGENT_ID = "pacing"
AGENT_LABEL = "Cognitive Load Researcher"

SYSTEM = """\
You are a Cognitive Load Researcher specialising in pediatric attention systems and how rapid \
visual transitions fragment attentional networks in developing brains. You apply Fernando's \
finite-state temporal string model: video pacing as strings over Σ = {s, n}, where string \
density |n|/t (cuts/min) is the primary attentional demand signal.

You have been given pacing signals for a video a child has watched. Use your tool to compute \
precise attention load metrics, then write 2–3 sentences from your research perspective on what \
the pacing means for this child's developing attention system.

End your response on a new line with exactly:
SCORE: <0-100>
(0 = smooth, age-appropriate pacing  |  100 = severely overstimulating for this age group)\
"""

TOOLS = [
    {
        "name": "compute_attention_load",
        "description": (
            "Compute the attentional demand from pacing signals using the Fernando FSM "
            "string density model. Returns how far the content is above the safe threshold "
            "for the child's age, and estimated total cut events."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "cuts_per_min": {"type": "number", "description": "Measured cuts per minute"},
                "age": {"type": "integer", "description": "Child's age"},
                "duration_sec": {"type": "integer", "description": "Video duration in seconds"},
            },
            "required": ["cuts_per_min", "age", "duration_sec"],
        },
    }
]


def _compute_attention_load(cuts_per_min: float, age: int, duration_sec: int) -> dict:
    band = get_age_band(age)
    max_cuts = band["max_cuts_per_min"]
    ratio = cuts_per_min / max(max_cuts, 1)

    if ratio <= 1.0:   risk = "within safe threshold"
    elif ratio <= 1.5: risk = "moderately above threshold"
    else:              risk = "severely above threshold"

    return {
        "string_density_cuts_per_min": round(cuts_per_min, 2),
        "safe_threshold_for_age": max_cuts,
        "ratio_to_threshold": round(ratio, 2),
        "risk_classification": risk,
        "total_estimated_cuts": int(cuts_per_min * duration_sec / 60),
        "fsm_note": (
            f"At {cuts_per_min}/min, burst sequences nᵏ where k>{int(cuts_per_min/2)} are likely — "
            f"exceeding working memory capacity for age {age}."
        ),
    }


def _handle_tool(name: str, inp: dict) -> dict:
    if name == "compute_attention_load":
        return _compute_attention_load(
            inp["cuts_per_min"], inp["age"], inp["duration_sec"]
        )
    return {"error": f"Unknown tool: {name}"}


async def pacing_agent(signals: dict, age: int):
    bracket = age_bracket_label(age)
    band = get_age_band(age)
    cuts = signals.get("cuts_per_min", 0)

    user = (
        f"Child age: {age} (bracket: {bracket}, safe limit: ≤{band['max_cuts_per_min']} cuts/min)\n"
        f"Cuts per minute: {cuts}\n"
        f"Duration: {signals.get('duration_sec', 0)}s\n\n"
        "Assess the pacing demands on this child's attention system."
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
