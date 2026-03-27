"""
Age-based thresholds and scoring weights for the pipeline.

Based on Fernando's FSM temporal string model (NALOMA 2022/23):
  string_density = |n|/t (cuts/min) over Σ = {s, n}
  >85 dB loudness → SMD -0.544 cognitive impairment (meta-analysis)
"""

AGE_BANDS: dict[str, dict] = {
    "0_to_2":   {"max_cuts_per_min": 3,  "max_volume_spike_pct": 0.05, "fsm_max_states": 3},
    "2_to_4":   {"max_cuts_per_min": 5,  "max_volume_spike_pct": 0.10, "fsm_max_states": 4},
    "5_to_7":   {"max_cuts_per_min": 8,  "max_volume_spike_pct": 0.15, "fsm_max_states": 5},
    "8_to_10":  {"max_cuts_per_min": 10, "max_volume_spike_pct": 0.20, "fsm_max_states": 7},
    "11_to_13": {"max_cuts_per_min": 12, "max_volume_spike_pct": 0.25, "fsm_max_states": 9},
    "14_to_16": {"max_cuts_per_min": 15, "max_volume_spike_pct": 0.30, "fsm_max_states": 12},
}

# Per-dimension weights by age bracket.
# Pacing matters most for young kids; manipulation matters more for teens.
# All 5 axes: pacing, sensory_overload, educational_deficit, manipulation, dopamine_cycling.
AGE_WEIGHTS: dict[str, dict] = {
    "0_to_2":   {"pacing": 2.0, "sensory_overload": 1.5, "educational_deficit": 0.8, "manipulation": 0.5, "dopamine_cycling": 1.2},
    "2_to_4":   {"pacing": 1.8, "sensory_overload": 1.4, "educational_deficit": 1.0, "manipulation": 0.8, "dopamine_cycling": 1.0},
    "5_to_7":   {"pacing": 1.5, "sensory_overload": 1.2, "educational_deficit": 1.2, "manipulation": 1.2, "dopamine_cycling": 0.9},
    "8_to_10":  {"pacing": 1.2, "sensory_overload": 1.0, "educational_deficit": 1.2, "manipulation": 1.3, "dopamine_cycling": 1.3},
    "11_to_13": {"pacing": 1.0, "sensory_overload": 0.9, "educational_deficit": 1.1, "manipulation": 1.5, "dopamine_cycling": 1.5},
    "14_to_16": {"pacing": 0.8, "sensory_overload": 0.8, "educational_deficit": 1.0, "manipulation": 1.8, "dopamine_cycling": 1.6},
}


def get_age_band_key(age: int) -> str:
    if age <= 2:    return "0_to_2"
    elif age <= 4:  return "2_to_4"
    elif age <= 7:  return "5_to_7"
    elif age <= 10: return "8_to_10"
    elif age <= 13: return "11_to_13"
    else:           return "14_to_16"


def get_age_band(age: int) -> dict:
    return AGE_BANDS[get_age_band_key(age)]


def age_bracket_label(age: int) -> str:
    return get_age_band_key(age).replace("_to_", "-")


def compute_brainrot_score(radar: dict, age: int) -> int:
    """Weighted average of all 5 radar axes, normalised to 0-100."""
    weights = AGE_WEIGHTS[get_age_band_key(age)]
    weighted_sum = sum(radar.get(dim, 50) * w for dim, w in weights.items())
    max_possible = sum(100 * w for w in weights.values())
    return max(0, min(100, round((weighted_sum / max_possible) * 100)))


def get_verdict(score: int) -> str:
    if score < 20: return "Enriching"
    if score < 40: return "Mostly Fine"
    if score < 60: return "Mixed"
    if score < 80: return "Concerning"
    return "Brain Rot"
