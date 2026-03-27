"""
Behavioral Neuroscientist — scores the `dopamine_cycling` radar axis.
Models the variable reward schedule to estimate dopamine cycling risk.
"""
import json
from multiagent_flow.client import async_client, MODEL, parse_score
from multiagent_flow.age_bands import age_bracket_label

AGENT_ID = "dopamine_cycling"
AGENT_LABEL = "Behavioral Neuroscientist"

SYSTEM = """\
You are a Behavioral Neuroscientist specialising in dopaminergic reward systems and how \
media environments shape the developing brain's reward circuitry. Your research focuses on \
variable reward schedules in children's content — how cut frequency, audio surprises, and \
content hooks combine to create slot-machine-like reward patterns that drive compulsive viewing.

You have been given pacing and audio signals for a video a child has watched. Use your tool \
to model the reward schedule, then write 2–3 sentences from your neuroscience perspective on \
what the reward structure means for this child's dopamine system.

End your response on a new line with exactly:
SCORE: <0-100>
(0 = healthy content cadence, no reward manipulation  |  100 = slot-machine-level dopamine cycling)\
"""

TOOLS = [
    {
        "name": "model_reward_schedule",
        "description": (
            "Model the variable reward schedule from pacing and audio signals. "
            "Computes average reward interval, classifies the schedule type (fixed vs variable ratio), "
            "and flags if the interval is in the high-addiction slot-machine range (<3s)."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "cuts_per_min": {"type": "number", "description": "Cuts per minute"},
                "volume_spike_frequency": {"type": "number", "description": "Volume spikes per minute"},
                "duration_sec": {"type": "integer", "description": "Video duration in seconds"},
            },
            "required": ["cuts_per_min", "volume_spike_frequency", "duration_sec"],
        },
    }
]


def _model_reward_schedule(cuts_per_min: float, volume_spike_frequency: float, duration_sec: int) -> dict:
    total_events_per_min = cuts_per_min + volume_spike_frequency
    avg_interval_sec = 60 / max(total_events_per_min, 0.1)

    schedule_type = (
        "continuous (low stimulation)"        if avg_interval_sec > 10 else
        "fixed-ratio (moderate stimulation)"  if avg_interval_sec > 4  else
        "variable-ratio (slot machine range)"
    )

    total_reward_events = int(total_events_per_min * duration_sec / 60)

    return {
        "avg_reward_interval_sec": round(avg_interval_sec, 2),
        "reward_schedule_type": schedule_type,
        "total_estimated_reward_events": total_reward_events,
        "slot_machine_risk": avg_interval_sec < 3,
        "neuroscience_note": (
            "Variable-ratio schedules under 3 seconds mirror slot machine mechanics — "
            "the most potent addiction-reinforcing pattern in behavioral neuroscience. "
            "Developing brains are especially vulnerable due to immature prefrontal inhibition."
            if avg_interval_sec < 3 else
            "Reward interval is above the high-risk threshold, though cumulative viewing time still matters."
        ),
    }


def _handle_tool(name: str, inp: dict) -> dict:
    if name == "model_reward_schedule":
        return _model_reward_schedule(
            inp["cuts_per_min"], inp["volume_spike_frequency"], inp["duration_sec"]
        )
    return {"error": f"Unknown tool: {name}"}


async def dopamine_agent(signals: dict, age: int):
    bracket = age_bracket_label(age)

    user = (
        f"Child age: {age} (bracket: {bracket})\n"
        f"Cuts per minute: {signals.get('cuts_per_min', 0)}\n"
        f"Volume spike frequency (per min): {signals.get('volume_spike_frequency', 0)}\n"
        f"Duration: {signals.get('duration_sec', 0)}s\n\n"
        "Model the reward schedule and assess dopamine cycling risk for this child."
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
