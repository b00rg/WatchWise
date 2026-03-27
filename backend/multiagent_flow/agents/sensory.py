"""
Sensory Integration Therapist — scores the `sensory_overload` radar axis.
Assesses the audiovisual environment against clinical sensory processing thresholds.
"""
import json
from multiagent_flow.client import async_client, MODEL, parse_score
from multiagent_flow.age_bands import get_age_band, age_bracket_label

AGENT_ID = "sensory_overload"
AGENT_LABEL = "Sensory Integration Therapist"

SYSTEM = """\
You are a Sensory Integration Therapist with clinical experience treating children with sensory \
processing difficulties. Your expertise is in how audiovisual environments impact a child's \
nervous system regulation — particularly how volume chaos, sudden loudness spikes, and sustained \
auditory unpredictability dysregulate developing sensory systems.

You have been given audio environment metrics for a video a child has watched. Use your tool to \
assess the sensory load against clinical thresholds for the child's age, then write 2–3 sentences \
from your therapeutic perspective on what you observe.

End your response on a new line with exactly:
SCORE: <0-100>
(0 = calm, well-regulated sensory environment  |  100 = severe sensory overwhelm risk)\
"""

TOOLS = [
    {
        "name": "assess_sensory_load",
        "description": (
            "Assess the sensory processing load from audio metrics against clinical thresholds "
            "for the child's age. Returns volume variance classification, spike severity, "
            "and whether age-specific thresholds are exceeded."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "volume_variance": {"type": "number", "description": "Fraction of frames at high volume (0.0–1.0)"},
                "spike_frequency": {"type": "number", "description": "Volume spike events per minute"},
                "age": {"type": "integer", "description": "Child's age"},
            },
            "required": ["volume_variance", "spike_frequency", "age"],
        },
    }
]


def _assess_sensory_load(volume_variance: float, spike_frequency: float, age: int) -> dict:
    band = get_age_band(age)
    max_spike_pct = band["max_volume_spike_pct"]

    variance_level = (
        "stable" if volume_variance < 0.3 else
        "moderate" if volume_variance < 0.6 else
        "jarring"
    )
    spike_level = (
        "calm" if spike_frequency < 5 else
        "moderate" if spike_frequency < 10 else
        "chaotic"
    )

    return {
        "volume_variance": round(volume_variance, 3),
        "volume_variance_level": variance_level,
        "spike_frequency_level": spike_level,
        "safe_variance_for_age": max_spike_pct,
        "threshold_exceeded": volume_variance > max_spike_pct,
        "db_overload_risk": volume_variance > 0.6,
        "clinical_note": (
            "Sustained exposure at this level is associated with sensory dysregulation and "
            "heightened cortisol response in children under 8." if spike_frequency > 10 else
            "Spike frequency is within manageable range, though cumulative exposure matters."
        ),
    }


def _handle_tool(name: str, inp: dict) -> dict:
    if name == "assess_sensory_load":
        return _assess_sensory_load(inp["volume_variance"], inp["spike_frequency"], inp["age"])
    return {"error": f"Unknown tool: {name}"}


async def sensory_agent(signals: dict, age: int):
    bracket = age_bracket_label(age)
    band = get_age_band(age)

    user = (
        f"Child age: {age} (bracket: {bracket}, safe volume spike threshold: {band['max_volume_spike_pct']})\n"
        f"Avg volume variance (0–1): {signals.get('avg_volume_variance', 0)}\n"
        f"Volume spike frequency (per min): {signals.get('volume_spike_frequency', 0)}\n"
        f"Duration: {signals.get('duration_sec', 0)}s\n\n"
        "Assess the sensory load of this video's audio environment for this child."
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
