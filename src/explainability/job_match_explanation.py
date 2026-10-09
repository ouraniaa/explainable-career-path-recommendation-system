"""
Creates a deterministic explanation of the occupation match shown to the user.

This file receives the results already produced by the recommendation pipeline 
and turns them into a readable explanation of the ESCO match, remaining skill
gaps, and supplementary labor-market evidence.
"""

def generate_job_match_explanation(occupation_name, recommendation_result):
    """
    Explain the already calculated match between the user and one occupation.
    """
    if not occupation_name:
        raise ValueError("occupation_name cannot be empty.")

    if not isinstance(recommendation_result, dict):
        raise ValueError("recommendation_result must be a dictionary.")

    required_fields = {
        "match_esco",
        "canonical_skill_count",
        "exact_match_count",
        "semantic_match_count",
        "missing_skill_count",
        "average_gap",
        "match_market",
        "both_skill_count",
        "market_reason"
    }

    missing_fields = (required_fields - set(recommendation_result.keys()))

    if missing_fields:
        raise ValueError(
            "recommendation_result is missing "
            f"required fields: {sorted(missing_fields)}"
        )

    match_esco = recommendation_result["match_esco"]
    canonical_skill_count = recommendation_result["canonical_skill_count"]
    exact_match_count = recommendation_result["exact_match_count"]
    semantic_match_count = recommendation_result["semantic_match_count"]
    missing_skill_count = recommendation_result["missing_skill_count"]
    average_gap = recommendation_result["average_gap"]
    match_market = recommendation_result["match_market"]
    both_skill_count = recommendation_result["both_skill_count"]
    market_reason = recommendation_result["market_reason"]

    if not 0.0 <= match_esco <= 1.0:
        raise ValueError("match_esco must be between 0 and 1.")

    if not 0.0 <= average_gap <= 1.0:
        raise ValueError("average_gap must be between 0 and 1.")

    if canonical_skill_count <= 0:
        raise ValueError("canonical_skill_count must be positive.")

    if exact_match_count < 0:
        raise ValueError("exact_match_count cannot be negative.")

    if semantic_match_count < 0:
        raise ValueError("semantic_match_count cannot be negative.")

    if missing_skill_count < 0:
        raise ValueError("missing_skill_count cannot be negative.")

    if both_skill_count < 0:
        raise ValueError("both_skill_count cannot be negative.")

    if (match_market is not None and not 0.0 <= match_market <= 1.0):
        raise ValueError("match_market must be between 0 and 1 when available.")

    match_esco_percent = (match_esco * 100)
    average_gap_percent = (average_gap * 100)

    match_market_percent = (match_market * 100
        if match_market is not None
        else None
    )

    matched_skill_count = (exact_match_count + semantic_match_count)

    esco_explanation = (
        f"For the occupation '{occupation_name}', "
        f"the user's current skill profile achieves "
        f"a MatchESCO of {match_esco_percent:.2f}%. "
        f"The canonical ESCO profile contains "
        f"{canonical_skill_count} skills. "
        f"{exact_match_count} required skills are "
        f"matched exactly, while "
        f"{semantic_match_count} required skills have "
        f"semantic matches in the user's profile. "
        f"{missing_skill_count} canonical skills remain "
        f"without coverage under the current matching "
        f"criterion. "
        f"The average residual skill gap is "
        f"{average_gap_percent:.2f}%."
    )

    if match_market is not None:
        market_explanation = (
            f"Labor-market evidence is also available "
            f"for this occupation. "
            f"The MatchMarket score is "
            f"{match_market_percent:.2f}%, calculated "
            f"from {both_skill_count} skills that are "
            f"supported by both the canonical ESCO "
            f"profile and the available labor-market "
            f"evidence. "
            f"This score is presented separately from "
            f"MatchESCO and is used as a supplementary "
            f"market-based signal."
        )

        market_available = True
    else:
        if market_reason:
            market_explanation = (
                f"A MatchMarket score is not available for this occupation. "
                f"Reason: {market_reason}. "
                f"The absence of MatchMarket does not affect the MatchESCO calculation."
            )
        else:
            market_explanation = (
                f"A MatchMarket score is not available for this occupation. "
                f"The absence of MatchMarket does not affect the MatchESCO calculation."
            )

        market_available = False

    explanation_text = (esco_explanation + " " + market_explanation)

    return {
        "explanation_type": "job_match",
        "occupation_name": occupation_name,
        "match_esco": match_esco,
        "match_esco_percent": match_esco_percent,
        "canonical_skill_count": canonical_skill_count,
        "exact_match_count": exact_match_count,
        "semantic_match_count": semantic_match_count,
        "matched_skill_count": matched_skill_count,
        "missing_skill_count": missing_skill_count,
        "average_gap": average_gap,
        "average_gap_percent": average_gap_percent,
        "market_available": market_available,
        "match_market": match_market,
        "match_market_percent": match_market_percent,
        "both_skill_count": both_skill_count,
        "market_reason": market_reason,
        "esco_explanation": esco_explanation,
        "market_explanation": market_explanation,
        "explanation_text": explanation_text
    }