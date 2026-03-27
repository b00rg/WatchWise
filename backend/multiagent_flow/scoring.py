"""
Scoring pipeline orchestrator.

score_video_stream() — async generator, yields SSE events for streaming to frontend.
score_video()        — consumes the stream silently, returns the final result dict.
                       Used by the history and creator batch endpoints.
"""
from multiagent_flow.agents.pacing import pacing_agent
from multiagent_flow.agents.sensory import sensory_agent
from multiagent_flow.agents.educational import educational_agent
from multiagent_flow.agents.manipulation import manipulation_agent
from multiagent_flow.agents.dopamine import dopamine_agent
from multiagent_flow.judge import judge_agent


async def score_video_stream(transcript: str, signals: dict, age: int, channel: str):
    """
    Runs agents sequentially so the frontend sees each specialist 'speak' in turn.
    Yields dicts; caller serialises to SSE.

    Event types:
      agent_start  — {"agent": str, "label": str}
      token        — {"agent": str, "text": str}
      tool_call    — {"agent": str, "tool": str}
      agent_done   — {"agent": str, "label": str, "score": int}
      final        — full result payload (brainrot_score, verdict, radar, summary, …)
    """
    radar: dict[str, int] = {}

    specialists = [
        pacing_agent(signals, age),
        sensory_agent(signals, age),
        educational_agent(transcript, channel, age),
        manipulation_agent(transcript, channel, age),
        dopamine_agent(signals, age),
    ]

    for agent_gen in specialists:
        async for event in agent_gen:
            yield event
            if event["type"] == "agent_done":
                radar[event["agent"]] = event["score"]

    async for event in judge_agent(radar, age, channel):
        yield event


async def score_video(transcript: str, signals: dict, age: int, channel: str) -> dict:
    """Non-streaming version — returns the final result dict. Used for batch endpoints."""
    result: dict = {}
    async for event in score_video_stream(transcript, signals, age, channel):
        if event["type"] == "final":
            result = event
    return result
