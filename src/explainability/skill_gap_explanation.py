"""
Creates a deterministic explanation for a single skill recommendation produced
by the Learning Priority module.

The explanation keeps canonical ESCO evidence, semantic effects, and
labor-market signals separate. ImprovementESCO remains the basis of the
learning-priority ranking, while RCA, Market Gap Severity, and
ImprovementMarket are reported only as supplementary evidence.
"""
def generate_skill_gap_explanation(ranked_skill):
    """
    Generates an explanation for one skill recommendation produced by the Learning Priority module.
    """
    if not isinstance(ranked_skill, dict):
        raise ValueError("ranked_skill must be a dictionary.")

    required_fields = {
        "skill_id",
        "skill_name",
        "relation_type",
        "match_type",
        "current_coverage",
        "residual_gap",
        "improvement_esco",
        "direct_improvement",
        "semantic_spillover",
        "semantic_dependency_ratio",
        "rca",
        "market_gap_severity",
        "improvement_market",
        "affected_esco_skill_count",
        "affected_esco_skills",
        "affected_market_skills"
    }

    missing_fields = (required_fields - set(ranked_skill.keys()))

    if missing_fields:
        raise ValueError(
            "ranked_skill is missing required fields: "
            f"{sorted(missing_fields)}"
        )
    
    skill_id = ranked_skill["skill_id"]
    skill_name = ranked_skill["skill_name"]
    relation_type = ranked_skill["relation_type"]
    match_type = ranked_skill["match_type"]
    current_coverage = ranked_skill["current_coverage"]
    residual_gap = ranked_skill["residual_gap"]
    improvement_esco = ranked_skill["improvement_esco"]
    direct_improvement = ranked_skill["direct_improvement"]
    semantic_spillover = ranked_skill["semantic_spillover"]
    semantic_dependency_ratio = ranked_skill["semantic_dependency_ratio"]
    rca = ranked_skill["rca"]
    market_gap_severity = ranked_skill["market_gap_severity"]
    improvement_market = ranked_skill["improvement_market"]
    affected_esco_skill_count = ranked_skill["affected_esco_skill_count"]
    affected_esco_skills = ranked_skill["affected_esco_skills"]
    affected_market_skills = ranked_skill["affected_market_skills"]

    if not skill_id:
        raise ValueError("skill_id cannot be empty.")

    if not skill_name:
        raise ValueError("skill_name cannot be empty.")

    if not 0.0 <= current_coverage <= 1.0:
        raise ValueError("current_coverage must be between 0 and 1.")

    if not 0.0 <= residual_gap <= 1.0:
        raise ValueError("residual_gap must be between 0 and 1.")

    if improvement_esco < 0.0:
        raise ValueError("improvement_esco cannot be negative.")

    if direct_improvement < 0.0:
        raise ValueError("direct_improvement cannot be negative.")

    if semantic_spillover < 0.0:
        raise ValueError("semantic_spillover cannot be negative.")

    if not (0.0 <= semantic_dependency_ratio <= 1.0):
        raise ValueError("semantic_dependency_ratio must be " "between 0 and 1.")

    if affected_esco_skill_count < 0:
        raise ValueError("affected_esco_skill_count cannot be negative.")

    if rca is not None and rca < 0.0:
        raise ValueError("rca cannot be negative.")

    if (market_gap_severity is not None and market_gap_severity < 0.):
        raise ValueError("market_gap_severity cannot be negative.")

    if (improvement_market is not None and improvement_market < 0.0):
        raise ValueError("improvement_market cannot be negative.")

    current_coverage_percent = (current_coverage * 100)
    residual_gap_percent = (residual_gap * 100)
    improvement_esco_percent = (improvement_esco * 100)
    direct_improvement_percent = (direct_improvement * 100)
    semantic_spillover_percent = (semantic_spillover * 100)
    semantic_dependency_percent = (semantic_dependency_ratio * 100)

    improvement_market_percent = (improvement_market * 100
        if improvement_market is not None
        else None
    )

    gap_explanation = (
        f"The skill '{skill_name}' is part of the "
        f"canonical ESCO profile of the target occupation "
        f"and is classified as '{relation_type}'. "
        f"Its current coverage from the user's existing "
        f"skills is {current_coverage_percent:.2f}%, "
        f"leaving a residual skill gap of "
        f"{residual_gap_percent:.2f}%."
    )

    improvement_explanation = (
        f"Adding '{skill_name}' to the user's profile is "
        f"estimated to increase MatchESCO by "
        f"{improvement_esco_percent:.2f} percentage points. "
        f"Of this improvement, "
        f"{direct_improvement_percent:.2f} percentage points "
        f"come from directly covering the skill itself, "
        f"while {semantic_spillover_percent:.2f} percentage "
        f"points come from improved semantic coverage of "
        f"other canonical ESCO skills."
    )

    if improvement_esco > 0.0:
        semantic_explanation = (
            f"The semantic dependency ratio is "
            f"{semantic_dependency_percent:.2f}%, meaning "
            f"that this proportion of the estimated "
            f"MatchESCO improvement is associated with "
            f"semantic spillover rather than only the "
            f"direct coverage of '{skill_name}'. "
            f"The simulated acquisition affects "
            f"{affected_esco_skill_count} canonical "
            f"ESCO skill entries in total."
        )

    else:
        semantic_explanation = (
            f"No positive MatchESCO improvement is "
            f"estimated for '{skill_name}', therefore "
            f"no semantic contribution is attributed "
            f"to its simulated acquisition."
        )

    market_available = (rca is not None or market_gap_severity is not None)

    if market_available:
        market_parts = []

        if rca is not None:
            market_parts.append(f"The skill has an RCA value of " f"{rca:.4f} for the target occupation.")

        if market_gap_severity is not None:
            market_parts.append(f"Its Market Gap Severity is " f"{market_gap_severity:.4f}.")

        if improvement_market is not None:
            market_parts.append(f"If the skill were acquired, the "
                f"estimated MatchMarket improvement would "
                f"be {improvement_market_percent:.2f} "
                f"percentage points."
            )

        market_parts.append("These market-based values are supplementary signals and do not determine the Learning Priority ranking, which is based on "
            "ImprovementESCO.")
        market_explanation = " ".join(market_parts)
    else:
        market_explanation = (
            f"No direct labor-market evidence is available "
            f"for '{skill_name}' in the current analytical profile. This does not affect its canonical ESCO-based recommendation."
        )

    explanation_text = " ".join([gap_explanation, improvement_explanation, semantic_explanation, market_explanation])

    return {
        "explanation_type": "skill_gap",
        "skill_id": skill_id,
        "skill_name": skill_name,
        "relation_type": relation_type,
        "match_type": match_type,
        "current_coverage": current_coverage,
        "current_coverage_percent": current_coverage_percent,
        "residual_gap": residual_gap,
        "residual_gap_percent": residual_gap_percent,
        "improvement_esco": improvement_esco,
        "improvement_esco_percent": improvement_esco_percent,
        "direct_improvement": direct_improvement,
        "direct_improvement_percent": direct_improvement_percent,
        "semantic_spillover": semantic_spillover,
        "semantic_spillover_percent": semantic_spillover_percent,
        "semantic_dependency_ratio": semantic_dependency_ratio,
        "semantic_dependency_percent": semantic_dependency_percent,
        "affected_esco_skill_count": affected_esco_skill_count,
        "affected_esco_skills": affected_esco_skills,
        "market_available": market_available,
        "rca": rca,
        "market_gap_severity": market_gap_severity,
        "improvement_market": improvement_market,
        "improvement_market_percent": improvement_market_percent,
        "affected_market_skills": affected_market_skills,
        "gap_explanation": gap_explanation,
        "improvement_explanation": improvement_explanation,
        "semantic_explanation": semantic_explanation,
        "market_explanation": market_explanation,
        "explanation_text": explanation_text
    }