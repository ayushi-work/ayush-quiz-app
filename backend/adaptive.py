"""Explainable adaptive difficulty engine.

Core idea: every quiz starts from the same baseline question.
After each answer we compute:

    performance = accuracy_score * 0.7 + speed_score * 0.3

- accuracy_score: weighted correctness over rolling window (last 5),
  recent answers weigh more so one mistake doesn't tank the student.
- speed_score: how fast vs expected_time for that difficulty.

Then map performance -> next difficulty:
    >85 expert, 70-85 hard, 50-70 medium, <50 easy
"""

from typing import List, Dict, Tuple

DIFFICULTIES = ["easy", "medium", "hard", "expert"]

TIERS = [
    {"id": 1, "name": "Rookie", "desc": "Easy questions"},
    {"id": 2, "name": "Learner", "desc": "Easy → Medium"},
    {"id": 3, "name": "Challenger", "desc": "Medium questions"},
    {"id": 4, "name": "Advanced", "desc": "Medium → Hard"},
    {"id": 5, "name": "Expert", "desc": "Hard questions"},
    {"id": 6, "name": "Master", "desc": "Expert-level questions"},
]

REWARDS = {"easy": 10, "medium": 20, "hard": 35, "expert": 50}

DIFFICULTY_ORDER = {d: i for i, d in enumerate(DIFFICULTIES)}


def speed_score(response_time: float, expected_time: float) -> float:
    expected_time = max(1.0, float(expected_time or 20))
    actual = max(0.5, float(response_time or expected_time))
    ratio = actual / expected_time
    if ratio <= 0.5:
        return 100.0
    if ratio <= 0.8:
        return 90.0
    if ratio <= 1.0:
        return 75.0
    if ratio <= 1.5:
        return 50.0
    if ratio <= 2.0:
        return 30.0
    return 15.0


def accuracy_score(history: List[bool], window: int = 5) -> float:
    """Weighted recent accuracy over last `window` answers (0-100)."""
    if not history:
        return 50.0  # neutral prior so first question matters but isn't harsh
    recent = history[-window:]
    # linear weights: oldest 1 ... newest N
    weights = list(range(1, len(recent) + 1))
    total = sum(weights)
    score = sum(w * (100.0 if c else 0.0) for w, c in zip(weights, recent))
    return round(score / total, 2)


def performance_score(history: List[bool], response_time: float, expected_time: float) -> Tuple[float, float, float]:
    acc = accuracy_score(history)
    spd = speed_score(response_time, expected_time)
    perf = round(acc * 0.7 + spd * 0.3, 2)
    return perf, acc, spd


def level_for_performance(perf: float) -> str:
    if perf > 85:
        return "expert"
    if perf >= 70:
        return "hard"
    if perf >= 50:
        return "medium"
    return "easy"


def student_band(overall_accuracy: float) -> str:
    """Beginner/Intermediate/Advanced/Expert band from spec section 3."""
    if overall_accuracy < 50:
        return "Beginner"
    if overall_accuracy < 70:
        return "Intermediate"
    if overall_accuracy <= 85:
        return "Advanced"
    return "Expert"


def allowed_difficulties(band_or_level: str) -> List[str]:
    mapping = {
        "Beginner": ["easy"],
        "Intermediate": ["easy", "medium"],
        "Advanced": ["medium", "hard"],
        "Expert": ["hard", "expert"],
        "easy": ["easy"],
        "medium": ["easy", "medium"],
        "hard": ["medium", "hard"],
        "expert": ["hard", "expert"],
    }
    return mapping.get(band_or_level, ["easy", "medium"])


def decide_next_difficulty(history: List[bool], response_time: float, expected_time: float) -> Dict:
    perf, acc, spd = performance_score(history, response_time, expected_time)
    level = level_for_performance(perf)
    band = student_band(acc)
    # speed influence note for explainability
    if history and history[-1]:
        if response_time <= expected_time * 0.6:
            note = "Correct + very fast → climbing faster."
        elif response_time <= expected_time:
            note = "Correct at good pace → difficulty increases gradually."
        else:
            note = "Correct but slow → difficulty increases cautiously."
    else:
        note = "Incorrect → serving an easier or conceptually similar question before progressing."
    return {
        "performance": perf,
        "accuracy_score": acc,
        "speed_score": spd,
        "next_difficulty": level,
        "band": band,
        "allowed": allowed_difficulties(level),
        "explanation": note,
    }


def tier_update(current_tier: int, progress: float, correct: bool,
                response_time: float, expected_time: float) -> Tuple[int, float, str]:
    """Return (new_tier, new_progress, note). Progress 0-100 within tier."""
    if correct:
        spd = speed_score(response_time, expected_time)
        if spd >= 90:
            delta = 25.0
            note = "Correct + Fast: tier progress +25"
        elif spd >= 75:
            delta = 16.0
            note = "Correct: tier progress +16"
        elif spd >= 50:
            delta = 10.0
            note = "Correct + Slow: tier progress +10"
        else:
            delta = 8.0
            note = "Correct but very slow: tier progress +8"
        progress += delta
    else:
        progress -= 12.0
        note = "Incorrect: tier progress −12 (no full reset)"
    new_tier = current_tier
    while progress >= 100 and new_tier < 6:
        progress -= 100
        new_tier += 1
        note += f" → Tier up to {new_tier}!"
    while progress < 0 and new_tier > 1:
        progress += 100
        new_tier -= 1
    progress = max(0.0, min(99.0 if new_tier < 6 else 100.0, progress))
    return new_tier, round(progress, 1), note


def reward_for(correct: bool, difficulty: str, response_time: float,
               expected_time: float, streak: int) -> Tuple[int, Dict]:
    if not correct:
        return 0, {"base": 0, "speed_bonus": 0, "streak_bonus": 0}
    base = REWARDS.get(difficulty, 10)
    speed_bonus = 5 if response_time <= expected_time * 0.6 else 0
    streak_bonus = 0
    if streak >= 5:
        streak_bonus = 25
    elif streak >= 3:
        streak_bonus = 10
    total = base + speed_bonus + streak_bonus
    return total, {"base": base, "speed_bonus": speed_bonus, "streak_bonus": streak_bonus}
