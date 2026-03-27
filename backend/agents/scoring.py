"""
Multi-agent scoring pipeline using Claude.
Three agents: content_agent, overstimulation_agent, judge_agent.
"""
import json, os, asyncio
import anthropic
from dotenv import load_dotenv

load_dotenv()
client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
MODEL = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-5")


def _call(system: str, user: str) -> str:
    msg = client.messages.create(
        model=MODEL,
        max_tokens=1024,
        system=system,
        messages=[{"role": "user", "content": user}],
    )
    return msg.content[0].text


def content_agent(transcript: str, channel: str, age: int) -> dict:
    system = (
        "You are a child development expert scoring digital content quality for kids. "
        "Return ONLY valid JSON with keys: educational_value (0-10), language_complexity (0-10 where 10=age-appropriate), "
        "clickbait_score (0-10), parasocial_score (0-10), fake_urgency_score (0-10), reasoning (string)."
    )
    user = f"""
Age of child: {age}
Channel: {channel}
Transcript excerpt: {transcript[:1000]}

Score this content for a {age}-year-old. Higher clickbait/parasocial/fake_urgency = more manipulative.
"""
    raw = _call(system, user)
    try:
        return json.loads(raw[raw.find("{"):raw.rfind("}")+1])
    except Exception:
        return {"educational_value": 5, "language_complexity": 5, "clickbait_score": 5,
                "parasocial_score": 5, "fake_urgency_score": 5, "reasoning": raw}


def overstimulation_agent(signals: dict, age: int) -> dict:
    system = (
        "You are a neuroscience researcher specializing in pediatric media effects. "
        "Return ONLY valid JSON with keys: pacing_score (0-10 where 10=extremely rapid/overstimulating), "
        "sensory_overload_score (0-10), dopamine_cycling_risk (0-10), reasoning (string)."
    )
    user = f"""
Age of child: {age}
Cuts per minute: {signals.get('cuts_per_min', 0)}
Avg volume variance (0-1): {signals.get('avg_volume_variance', 0)}
Volume spike frequency (per min): {signals.get('volume_spike_frequency', 0)}
Video duration (seconds): {signals.get('duration_sec', 0)}

Reference: For a {age}-year-old, >3 cuts/min is high pacing, >8 cuts/min is extreme.
Score the overstimulation risk based on these signals.
"""
    raw = _call(system, user)
    try:
        return json.loads(raw[raw.find("{"):raw.rfind("}")+1])
    except Exception:
        return {"pacing_score": 5, "sensory_overload_score": 5, "dopamine_cycling_risk": 5, "reasoning": raw}


def judge_agent(content: dict, overstim: dict, channel: str, age: int) -> dict:
    system = (
        "You are a final judge synthesizing child development and neuroscience assessments of digital content. "
        "Return ONLY valid JSON with keys: "
        "brainrot_score (0-100, where 0=highly enriching, 100=maximum brainrot), "
        "radar (object with keys: pacing, sensory_overload, educational_value, manipulation, dopamine_cycling — each 0-10), "
        "verdict (one of: Enriching | Mostly Fine | Mixed | Concerning | Brain Rot), "
        "summary (2-3 sentence plain-English explanation for a parent)."
    )
    user = f"""
Child age: {age}
Channel: {channel}
Content agent findings: {json.dumps(content)}
Overstimulation agent findings: {json.dumps(overstim)}

Synthesize into a final BrainRot score and radar breakdown.
"""
    raw = _call(system, user)
    try:
        return json.loads(raw[raw.find("{"):raw.rfind("}")+1])
    except Exception:
        return {
            "brainrot_score": 50,
            "radar": {"pacing": 5, "sensory_overload": 5, "educational_value": 5, "manipulation": 5, "dopamine_cycling": 5},
            "verdict": "Mixed",
            "summary": raw,
        }


async def score_video(transcript: str, signals: dict, age: int, channel: str) -> dict:
    content = await asyncio.to_thread(content_agent, transcript, channel, age)
    overstim = await asyncio.to_thread(overstimulation_agent, signals, age)
    judge = await asyncio.to_thread(judge_agent, content, overstim, channel, age)
    return {
        "brainrot_score": judge.get("brainrot_score", 50),
        "verdict": judge.get("verdict", "Mixed"),
        "summary": judge.get("summary", ""),
        "radar": judge.get("radar", {}),
        "details": {"content": content, "overstimulation": overstim},
    }
