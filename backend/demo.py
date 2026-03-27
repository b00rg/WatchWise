"""
Demo script — runs the full multiagent scoring pipeline with fake pipeline data.
No YouTube URL or ffmpeg needed.

Run from the backend/ directory:
    python demo.py
"""
import asyncio

from multiagent_flow.scoring import score_video_stream

# ── Fake pipeline output (what video.py would normally produce) ────────────────

MOCK_SIGNALS = {
    "cuts_per_min": 42,
    "avg_volume_variance": 0.71,
    "volume_spike_frequency": 14,
    "duration_sec": 487,
}

MOCK_TRANSCRIPT = """
Oh my gosh you guys are NOT gonna believe what's in this mystery box!! Smash that like button
RIGHT NOW before we open it!! I love you guys SO much, you're literally my favourite people in
the whole world!! HURRY because this is a LIMITED TIME unboxing and everyone is watching!!
Wait for it... wait for it... OH WOW that is INSANE!! You won't believe what just happened!!
Comment below if you want to see more!! Don't forget to ring the bell so you NEVER miss a video!!
This is the CRAZIEST thing I've ever seen and if you're not subscribed you're literally missing out!!
"""

MOCK_CHANNEL = "CrazyUnboxKidz"
MOCK_AGE = 7

# ── Pretty printer ─────────────────────────────────────────────────────────────

COLOURS = {
    "pacing":               "\033[94m",   # blue
    "sensory_overload":     "\033[95m",   # magenta
    "educational_deficit":  "\033[92m",   # green
    "manipulation":         "\033[91m",   # red
    "dopamine_cycling":     "\033[93m",   # yellow
    "judge":                "\033[97m",   # white
}
RESET = "\033[0m"
BOLD  = "\033[1m"
DIM   = "\033[2m"


def colour(agent: str) -> str:
    return COLOURS.get(agent, "\033[96m")


async def run_demo():
    print(f"\n{BOLD}RotCheck Demo{RESET}")
    print(f"{DIM}Video: {MOCK_CHANNEL} | Age: {MOCK_AGE} | Duration: {MOCK_SIGNALS['duration_sec']}s{RESET}")
    print(f"{DIM}Cuts/min: {MOCK_SIGNALS['cuts_per_min']} | Volume variance: {MOCK_SIGNALS['avg_volume_variance']}{RESET}\n")
    print("─" * 60)

    current_agent = None

    async for event in score_video_stream(
        transcript=MOCK_TRANSCRIPT,
        signals=MOCK_SIGNALS,
        age=MOCK_AGE,
        channel=MOCK_CHANNEL,
    ):
        t = event["type"]

        if t == "agent_start":
            current_agent = event["agent"]
            c = colour(current_agent)
            print(f"\n{c}{BOLD}[ {event['label']} ]{RESET}")

        elif t == "token":
            c = colour(event["agent"])
            print(f"{c}{event['text']}{RESET}", end="", flush=True)

        elif t == "tool_call":
            c = colour(event["agent"])
            print(f"\n{DIM}{c}  → calling tool: {event['tool']}{RESET}")

        elif t == "agent_done":
            c = colour(event["agent"])
            score = event["score"]
            bar = "█" * (score // 5) + "░" * (20 - score // 5)
            print(f"\n{c}  SCORE: {BOLD}{score}/100{RESET} {c}[{bar}]{RESET}\n")

        elif t == "final":
            print("\n" + "─" * 60)
            verdict_colour = {
                "Enriching": "\033[92m", "Mostly Fine": "\033[92m",
                "Mixed": "\033[93m", "Concerning": "\033[91m", "Brain Rot": "\033[91m",
            }.get(event.get("verdict", ""), "\033[97m")

            print(f"\n{BOLD}FINAL BRAINROT SCORE: {verdict_colour}{event['brainrot_score']}/100{RESET}")
            print(f"{verdict_colour}{BOLD}{event['verdict']}{RESET}  |  age {event['age_bracket']}  |  pacing risk: {event['fsm_risk_level']}")
            print(f"\n{DIM}{event['summary']}{RESET}\n")
            print(f"{BOLD}Radar:{RESET}")
            for dim, score in event["radar"].items():
                bar = "█" * (score // 5) + "░" * (20 - score // 5)
                c = colour(dim)
                print(f"  {c}{dim:<22}{RESET} {score:>3}/100  {c}[{bar}]{RESET}")
            print()


if __name__ == "__main__":
    asyncio.run(run_demo())
