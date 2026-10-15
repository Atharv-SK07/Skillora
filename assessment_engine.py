"""Skillora Assessment & Scoring Engine.

Core business logic for:
1. Mapping raw quiz performance to a 1-5 proficiency scale.
2. Computing initial combined skill estimate: S = 0.7Q + 0.3A.
3. Detecting self-assessment vs quiz discrepancies (|Q - A| >= 2).
4. Computing importance-weighted career readiness (capped at target level).
5. Computing assessment coverage and determining provisional readiness status.
"""

from typing import Dict, List, Optional, Tuple, Any

# ---------------------------------------------------------------------------
# Proficiency Scale Definition:
# Level 0: Unassessed (Reserved exclusively - does not mean zero skill)
# Level 1: Novice (Basic awareness, requires guidance)
# Level 2: Advanced Beginner (Practical fundamental knowledge)
# Level 3: Competent (Independent working proficiency)
# Level 4: Proficient (Deep understanding and problem-solving)
# Level 5: Expert (Mastery, architecture, and edge-case handling)
# ---------------------------------------------------------------------------

PROFICIENCY_LEVELS = {
    0: "Unassessed",
    1: "Novice",
    2: "Advanced Beginner",
    3: "Competent",
    4: "Proficient",
    5: "Expert"
}


def map_score_to_proficiency(percentage: float) -> int:
    """Map raw quiz percentage (0.0 to 100.0) to a proficiency level 1–5.
    
    Documented Scoring Policy:
    - 0% <= score < 40%: Level 1 (Novice)
    - 40% <= score < 60%: Level 2 (Advanced Beginner)
    - 60% <= score < 75%: Level 3 (Competent)
    - 75% <= score < 90%: Level 4 (Proficient)
    - 90% <= score <= 100%: Level 5 (Expert)
    
    Level 0 is NOT returned by this function, as any completed quiz attempt
    represents an active assessment (Level 0 is reserved for unassessed state).
    
    Raises:
        ValueError: If percentage is not within [0.0, 100.0].
    """
    if percentage is None or not (0.0 <= percentage <= 100.0):
        raise ValueError(f"Percentage must be between 0.0 and 100.0, got: {percentage}")

    if percentage < 40.0:
        return 1
    elif percentage < 60.0:
        return 2
    elif percentage < 75.0:
        return 3
    elif percentage < 90.0:
        return 4
    else:
        return 5


def calculate_combined_estimate(quiz_proficiency: Optional[int],
                                self_assessed_level: Optional[int]) -> Optional[float]:
    """Calculate the initial combined skill estimate: S = 0.7Q + 0.3A.
    
    Rules:
    - Q: Quiz-derived proficiency (1-5)
    - A: Self-assessed proficiency (1-5)
    - Missing data or Level 0 (unassessed) must NOT be silently replaced with 0.
    - If either input is missing, None is returned.
    
    Returns:
        float rounded to 2 decimal places, or None if inputs are incomplete.
    """
    if quiz_proficiency is None or self_assessed_level is None:
        return None
    if not (1 <= quiz_proficiency <= 5):
        return None
    if not (1 <= self_assessed_level <= 5):
        return None

    s = 0.7 * float(quiz_proficiency) + 0.3 * float(self_assessed_level)
    return round(s, 2)


def check_discrepancy(quiz_proficiency: Optional[int],
                      self_assessed_level: Optional[int]) -> Tuple[bool, Optional[str]]:
    """Flag a discrepancy when |Q - A| >= 2.
    
    Prompts user awareness and feedback, without forcing a retake.
    
    Returns:
        (has_discrepancy, explanation_message)
    """
    if quiz_proficiency is None or self_assessed_level is None:
        return False, None
    if not (1 <= quiz_proficiency <= 5 and 1 <= self_assessed_level <= 5):
        return False, None

    diff = quiz_proficiency - self_assessed_level
    abs_diff = abs(diff)

    if abs_diff >= 2:
        if diff < 0:
            # self_assessed > quiz
            msg = (
                f"Discrepancy detected (|Q - A| = {abs_diff}): You self-rated at Level {self_assessed_level} "
                f"({PROFICIENCY_LEVELS[self_assessed_level]}), but the quiz indicated Level {quiz_proficiency} "
                f"({PROFICIENCY_LEVELS[quiz_proficiency]}). Consider reinforcing foundational concepts with targeted practice."
            )
        else:
            # quiz > self_assessed
            msg = (
                f"Discrepancy detected (|Q - A| = {abs_diff}): You rated yourself at Level {self_assessed_level} "
                f"({PROFICIENCY_LEVELS[self_assessed_level]}), but scored Level {quiz_proficiency} "
                f"({PROFICIENCY_LEVELS[quiz_proficiency]}) on the quiz! Your knowledge is stronger than you thought."
            )
        return True, msg

    return False, "Self-assessment and quiz performance are closely aligned."


def calculate_career_readiness(skill_requirements: List[Dict[str, Any]],
                               user_estimates: Dict[int, float]) -> Dict[str, Any]:
    """Calculate career readiness and assessment coverage.
    
    Rules:
    1. Unassessed skills (not in user_estimates, or value 0) are excluded from the readiness numerator and denominator.
    2. Assessment coverage = (sum of weights of assessed skills) / (total weight of all required skills) * 100.
    3. Readiness uses importance-weighted skill attainment capped at each skill's target level:
       Attainment_i = min(1.0, Estimate_i / Target_i)
       Readiness = [ sum(Weight_i * Attainment_i) / sum(Weight_i for assessed) ] * 100
    4. If coverage < 70%, readiness is flagged as PROVISIONAL.
    5. If no skills are assessed, readiness is 0.0 (or None) with 0.0% coverage and is_provisional=True.
    
    Args:
        skill_requirements: List of dicts with keys:
            - 'skill_id': int
            - 'target_level': int (1-5)
            - 'importance_weight': float (> 0)
            - 'is_core': int (0 or 1, optional)
            - 'skill_name': str (optional)
        user_estimates: Mapping of skill_id -> user's current proficiency estimate (float/int 1.0-5.0).
            Unassessed skills should be omitted or have value <= 0.
            
    Returns:
        dict with:
            - 'coverage_percentage': float (0.0 to 100.0)
            - 'readiness_score': float (0.0 to 100.0)
            - 'is_provisional': bool (True if coverage < 70.0%)
            - 'total_weight': float
            - 'assessed_weight': float
            - 'assessed_skills_count': int
            - 'total_skills_count': int
            - 'breakdown': list of detailed skill attainment dicts
    """
    total_skills_count = len(skill_requirements)
    if total_skills_count == 0:
        return {
            'coverage_percentage': 0.0,
            'readiness_score': 0.0,
            'is_provisional': True,
            'total_weight': 0.0,
            'assessed_weight': 0.0,
            'assessed_skills_count': 0,
            'total_skills_count': 0,
            'breakdown': []
        }

    total_weight = sum(req['importance_weight'] for req in skill_requirements)
    assessed_weight = 0.0
    weighted_attainment_sum = 0.0
    assessed_count = 0
    breakdown = []

    for req in skill_requirements:
        s_id = req['skill_id']
        target = float(req['target_level'])
        weight = float(req['importance_weight'])
        estimate = user_estimates.get(s_id)

        is_assessed = (estimate is not None and estimate > 0)
        attainment_ratio = 0.0

        if is_assessed:
            assessed_count += 1
            assessed_weight += weight
            # Capped attainment at target level
            attainment_ratio = min(1.0, float(estimate) / target)
            weighted_attainment_sum += weight * attainment_ratio

        breakdown.append({
            'skill_id': s_id,
            'skill_name': req.get('skill_name', f'Skill {s_id}'),
            'target_level': target,
            'importance_weight': weight,
            'is_core': req.get('is_core', 1),
            'current_estimate': estimate if is_assessed else 0,
            'is_assessed': is_assessed,
            'attainment_ratio': round(attainment_ratio, 4)
        })

    # Coverage calculation
    coverage = (assessed_weight / total_weight * 100.0) if total_weight > 0 else 0.0

    # Readiness calculation (over assessed weight only, excluding unassessed)
    if assessed_weight > 0:
        readiness = (weighted_attainment_sum / assessed_weight) * 100.0
    else:
        readiness = 0.0

    is_provisional = coverage < 70.0

    return {
        'coverage_percentage': round(coverage, 1),
        'readiness_score': round(readiness, 1),
        'is_provisional': is_provisional,
        'total_weight': round(total_weight, 2),
        'assessed_weight': round(assessed_weight, 2),
        'assessed_skills_count': assessed_count,
        'total_skills_count': total_skills_count,
        'breakdown': breakdown
    }
