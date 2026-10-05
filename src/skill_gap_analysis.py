"""
Builds the skill-gap view from the detailed ESCO matching results.

The module converts each required skill into a gap value based on its current coverage.
Only skills with no match are counted as missing; semantic matches keep their remaining
partial gap instead of being treated as either fully present or completely absent.
This keeps the gap analysis consistent with the main ESCO matching logic.
"""
import math

def calculate_skill_gaps(esco_details):
    """
    Calculates skill gaps from the canonical ESCO skill details.
    Gap(s, U) = 1 - Coverage(s, U)

    Uses previously calculated coverage values.
    """
    if esco_details is None:
        raise ValueError("esco_details cannot be None.")

    skill_gaps = []

    exact_count = 0
    semantic_count = 0
    missing_count = 0

    seen_skill_ids = set()

    for detail in esco_details:
        skill_id = detail["required_skill_id"]
        skill_name = detail["required_skill_name"]

        coverage = float(detail["coverage"])

        match_type = detail["match_type"]

        if skill_id in seen_skill_ids:
            raise ValueError(f"Duplicate canonical skill: {skill_id}")

        seen_skill_ids.add(skill_id)

        if (not math.isfinite(coverage) or coverage < 0.0 or coverage > 1.0):
            raise ValueError(
                f"Invalid coverage for skill {skill_id}: "
                f"{coverage}"
            )

        if match_type not in {
            "exact",
            "semantic",
            "none"
        }:
            raise ValueError(f"Invalid match type: {match_type}")

        gap = 1.0 - coverage

        if match_type == "exact":
            exact_count += 1
        elif match_type == "semantic":
            semantic_count += 1
        else:
            missing_count += 1

        skill_gaps.append({
            "skill_id": skill_id,
            "skill_name": skill_name,
            "relation_type": detail.get(
                "relation_type"
            ),
            "match_type": match_type,
            "best_user_skill_id": detail.get(
                "best_user_skill_id"
            ),
            "best_user_skill_name": detail.get(
                "best_user_skill_name"
            ),
            "coverage": coverage,
            "gap": gap
        })

    skill_gaps.sort(
        key=lambda item: (
            -item["gap"],
            item["skill_name"].lower()
        )
    )

    canonical_skill_count = len(skill_gaps)

    average_gap = (sum(item["gap"] for item in skill_gaps) / canonical_skill_count
        if canonical_skill_count > 0
        else None
    )

    return {
        "canonical_skill_count": canonical_skill_count,
        "exact_count": exact_count,
        "semantic_count": semantic_count,
        "missing_count": missing_count,
        "average_gap": average_gap,
        "skill_gaps": skill_gaps
    }