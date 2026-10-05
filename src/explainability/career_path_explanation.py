"""
Creates deterministic explanations for career transition, career discovery,
career comparisons, and personalized learning roadmaps.

This file was created to keep explainability separate from the recommendation
algorithms themselves. 
Keeping the explanations deterministic is important for the thesis because every
statement can be traced back to an already calculated value.

For Career Transition, structural Jaccard similarity is explained only as
candidate-generation evidence, while the final ranking remains based on MatchESCO.
For Career Discovery, occupations are explained directly from the user's MatchESCO.
Roadmap explanations describe the greedy sequential simulation without presenting
it as a globally optimal learning path.
"""
def generate_career_transition_explanation(transition_result):
    """
    Explain the already calculated Career Transition recommendations.
    """
    if not isinstance(transition_result, dict):
        raise ValueError("transition_result must be a dictionary.")

    required_fields = {
        "mode",
        "current_occupation_id",
        "current_occupation_name",
        "current_occupation_isco_group",
        "structural_similarity_method",
        "structural_filtering_role",
        "final_ranking_criterion",
        "recommendations"
    }

    missing_fields = (required_fields - set(transition_result.keys()))

    if missing_fields:
        raise ValueError("transition_result is missing required fields: "
            f"{sorted(missing_fields)}"
        )

    if transition_result["mode"] != "career_transition":
        raise ValueError("Expected a career_transition result.")

    recommendations = transition_result["recommendations"]

    if not recommendations:
        raise ValueError("No career transition recommendations available.")

    current_occupation_name = transition_result["current_occupation_name"]

    general_explanation = (
        f"Career transition candidates were first selected "
        f"according to their structural similarity with the "
        f"user's current occupation, "
        f"'{current_occupation_name}'. "
        f"Structural similarity was measured using "
        f"unweighted Jaccard similarity over canonical "
        f"ESCO skill requirements. "
        f"The structurally related candidates were then "
        f"evaluated against the user's actual skill profile. "
        f"The final user-specific ranking is based on "
        f"MatchESCO."
    )

    explained_recommendations = []

    for item in recommendations:
        required_item_fields = {
            "rank",
            "occupation_id",
            "occupation_name",
            "isco_group",
            "structural_rank",
            "occupation_similarity",
            "shared_skill_count",
            "union_skill_count",
            "match_esco",
            "match_market",
            "market_reason",
            "missing_skill_count",
            "canonical_skill_count"
        }

        missing_item_fields = (required_item_fields - set(item.keys()))

        if missing_item_fields:
            raise ValueError("Career transition recommendation is missing required fields: "
                f"{sorted(missing_item_fields)}"
            )

        occupation_similarity_percent = (item["occupation_similarity"] * 100)

        match_esco_percent = (item["match_esco"] * 100)

        match_market_percent = (item["match_market"] * 100
            if item["match_market"] is not None
            else None
        )

        structural_explanation = (
            f"'{item['occupation_name']}' has structural "
            f"rank {item['structural_rank']} relative to "
            f"'{current_occupation_name}'. "
            f"The two occupations share "
            f"{item['shared_skill_count']} canonical ESCO "
            f"skills out of "
            f"{item['union_skill_count']} distinct skills "
            f"across their combined canonical profiles, "
            f"resulting in an occupation Jaccard similarity "
            f"of {occupation_similarity_percent:.2f}%."
        )

        user_match_explanation = (
            f"For the user's current skill profile, "
            f"'{item['occupation_name']}' has a MatchESCO "
            f"of {match_esco_percent:.2f}%. Its canonical ESCO profile contains "
            f"{item['canonical_skill_count']} skills, with "
            f"{item['missing_skill_count']} currently uncovered canonical skills."
        )

        if item["match_market"] is not None:
            if item["match_market"] == 0.0:
                market_explanation = (
                    f"MatchMarket is available for this occupation, but the user's current profile has no measured "
                    f"market-based coverage under the current MatchMarket definition. This market-based result is supplementary and "
                    f"does not determine the final career-transition ranking."
                )

            else:
                market_explanation = (
                    f"MatchMarket is "
                    f"{match_market_percent:.2f}%. This market-based score is shown as supplementary evidence and does not determine the final career-transition ranking."
                )

            market_available = True

        else:
            reason = item["market_reason"]

            if reason:
                market_explanation = (f"MatchMarket is not available for "
                    f"this occupation. Reason: {reason}. This does not affect the MatchESCO ranking."
                )
            else:
                market_explanation = (
                    f"MatchMarket is not available for this occupation. This does not affect the MatchESCO ranking."
                )

            market_available = False

        explanation_text = " ".join([structural_explanation, user_match_explanation, market_explanation])

        explained_recommendations.append({
            "rank": item["rank"],
            "occupation_id": item["occupation_id"],
            "occupation_name": item["occupation_name"],
            "isco_group": item["isco_group"],
            "structural_rank": item["structural_rank"],
            "occupation_similarity": item["occupation_similarity"],
            "occupation_similarity_percent": occupation_similarity_percent,
            "shared_skill_count": item["shared_skill_count"],
            "union_skill_count": item["union_skill_count"],
            "match_esco": item["match_esco"],
            "match_esco_percent": match_esco_percent,
            "market_available": market_available,
            "match_market": item["match_market"],
            "match_market_percent": match_market_percent,
            "missing_skill_count": item["missing_skill_count"],
            "structural_explanation": structural_explanation,
            "user_match_explanation": user_match_explanation,
            "market_explanation": market_explanation,
            "explanation_text": explanation_text
        })

    return {
        "explanation_type": "career_transition",
        "current_occupation_id": transition_result["current_occupation_id"],
        "current_occupation_name": current_occupation_name,
        "ranking_criterion": transition_result["final_ranking_criterion"],
        "general_explanation": general_explanation,
        "recommendations": explained_recommendations
    }


def generate_career_discovery_explanation(discovery_result):
    """
    Explain Career Discovery recommendations when no current occupation is provided.

    Discovery evaluates the supported occupations directly against the user's skill
    profile, so there is no structural occupation-similarity stage. The explanation
    therefore focuses on MatchESCO and keeps MatchMarket as separate supporting evidence.
    """
    if not isinstance(discovery_result, dict):
        raise ValueError("discovery_result must be a dictionary.")

    required_fields = {
        "mode",
        "candidate_pool",
        "candidate_count",
        "final_ranking_criterion",
        "recommendations"
    }

    missing_fields = (required_fields - set(discovery_result.keys()))

    if missing_fields:
        raise ValueError("discovery_result is missing required fields: "
            f"{sorted(missing_fields)}"
        )

    if discovery_result["mode"] != "career_discovery":
        raise ValueError("Expected a career_discovery result.")

    recommendations = discovery_result["recommendations"]

    if not recommendations:
        raise ValueError("No career discovery recommendations available.")

    general_explanation = (
        f"No current occupation was provided, so the system operated in Career Discovery mode. "
        f"{discovery_result['candidate_count']} supported occupations were evaluated directly against the user's current skill profile. "
        f"The final ranking is based on MatchESCO. MatchMarket is shown separately where sufficient labor-market evidence is available."
    )

    explained_recommendations = []

    for item in recommendations:
        match_esco_percent = (item["match_esco"] * 100)

        match_market_percent = (item["match_market"] * 100
            if item["match_market"] is not None
            else None
        )

        match_explanation = (
            f"'{item['occupation_name']}' is ranked "
            f"{item['rank']} in Career Discovery. "
            f"The user's current skill profile achieves "
            f"a MatchESCO of "
            f"{match_esco_percent:.2f}% for this occupation. "
            f"The canonical profile contains "
            f"{item['canonical_skill_count']} skills, with "
            f"{item['missing_skill_count']} currently "
            f"uncovered canonical skills."
        )

        if item["match_market"] is not None:
            if item["match_market"] == 0.0:
                market_explanation = (
                    f"MatchMarket is available for this occupation, but the user's current profile has no measured market-based coverage under the current MatchMarket definition. This result is supplementary and does not affect the Career Discovery ranking."
                )
            else:
                market_explanation = (
                    f"MatchMarket is "
                    f"{match_market_percent:.2f}%. This value is supplementary and does not affect the Career Discovery ranking."
                )
            market_available = True

        else:
            reason = item["market_reason"]

            if reason:
                market_explanation = (
                    f"MatchMarket is not available. "
                    f"Reason: {reason}."
                )
            else:
                market_explanation = ("MatchMarket is not available for this occupation.")
            market_available = False

        explanation_text = (match_explanation + " " + market_explanation)

        explained_recommendations.append({
            "rank": item["rank"],
            "occupation_id": item["occupation_id"],
            "occupation_name": item["occupation_name"],
            "isco_group": item["isco_group"],
            "match_esco": item["match_esco"],
            "match_esco_percent": match_esco_percent,
            "market_available": market_available,
            "match_market": item["match_market"],
            "match_market_percent": match_market_percent,
            "missing_skill_count": item["missing_skill_count"],
            "match_explanation": match_explanation,
            "market_explanation": market_explanation,
            "explanation_text": explanation_text
        })

    return {
        "explanation_type": "career_discovery",
        "candidate_pool": discovery_result["candidate_pool"],
        "candidate_count": discovery_result["candidate_count"],
        "ranking_criterion": discovery_result["final_ranking_criterion"],
        "general_explanation": general_explanation,
        "recommendations": explained_recommendations
    }


def generate_career_path_comparison_explanation(preferred_candidate, alternative_candidate):
    """
    Explain why one already evaluated career candidate appears above another.

    The comparison is based on the existing MatchESCO values and, when available,
    reports structural similarity separately. It explains the system's ranking only
    and does not claim that one occupation is objectively better than another.
    """
    if not isinstance(preferred_candidate, dict):
        raise ValueError("preferred_candidate must be a dictionary.")

    if not isinstance(alternative_candidate, dict):
        raise ValueError("alternative_candidate must be a dictionary.")

    required_fields = {
        "occupation_name",
        "match_esco"
    }

    for label, candidate in [
        ("preferred_candidate", preferred_candidate),
        ("alternative_candidate", alternative_candidate)
    ]:
        missing_fields = (required_fields - set(candidate.keys()))

        if missing_fields:
            raise ValueError(
                f"{label} is missing required fields: "
                f"{sorted(missing_fields)}"
            )

    preferred_match = (preferred_candidate["match_esco"])
    alternative_match = (alternative_candidate["match_esco"])
    preferred_percent = (preferred_match * 100)
    alternative_percent = (alternative_match * 100)
    difference = (preferred_match - alternative_match)
    difference_percentage_points = (difference * 100)

    if preferred_match < alternative_match:
        raise ValueError("preferred_candidate must have a MatchESCO greater than or equal to alternative_candidate.")

    comparison_text = (
        f"'{preferred_candidate['occupation_name']}' appears "
        f"above '{alternative_candidate['occupation_name']}' "
        f"in the user-specific ranking because its "
        f"MatchESCO is {preferred_percent:.2f}%, compared "
        f"with {alternative_percent:.2f}% for "
        f"'{alternative_candidate['occupation_name']}'. "
        f"The difference is "
        f"{difference_percentage_points:.2f} percentage "
        f"points. This comparison explains the ranking produced by the current skill-matching criterion and does not imply that one occupation is objectively better than the other."
    )

    structural_comparison = None

    if ("occupation_similarity" in preferred_candidate and "occupation_similarity" in alternative_candidate):
        preferred_jaccard = (preferred_candidate["occupation_similarity"] * 100)
        alternative_jaccard = (alternative_candidate["occupation_similarity"] * 100)

        structural_comparison = (
            f"Structural similarity is reported separately: "
            f"'{preferred_candidate['occupation_name']}' "
            f"has an occupation Jaccard of "
            f"{preferred_jaccard:.2f}%, while "
            f"'{alternative_candidate['occupation_name']}' "
            f"has {alternative_jaccard:.2f}%. "
            f"These structural values were used for "
            f"candidate generation, not for the final "
            f"user-specific ranking."
        )
        comparison_text = (comparison_text + " " + structural_comparison)

    return {
        "explanation_type": "career_path_comparison",
        "preferred_occupation": preferred_candidate["occupation_name"],
        "alternative_occupation": alternative_candidate["occupation_name"],
        "preferred_match_esco": preferred_match,
        "alternative_match_esco": alternative_match,
        "match_difference": difference,
        "match_difference_percentage_points": difference_percentage_points,
        "structural_comparison": structural_comparison,
        "explanation_text": comparison_text
    }


def generate_career_skill_roadmap_explanation(roadmap_result):
    """
    Explain the already generated Personalized Career Skill Roadmap.

    The roadmap is produced beforehand by the greedy sequential roadmap module.
    """
    if not isinstance(roadmap_result, dict):
        raise ValueError("roadmap_result must be a dictionary.")

    required_fields = {
        "occupation_id",
        "selection_method",
        "selection_strategy",
        "initial_match_esco",
        "initial_match_market",
        "roadmap_step_count",
        "roadmap_steps",
        "final_match_esco",
        "final_match_market",
        "remaining_candidate_skill_count"
    }

    missing_fields = (required_fields - set(roadmap_result.keys()))

    if missing_fields:
        raise ValueError("roadmap_result is missing required fields: "
            f"{sorted(missing_fields)}"
        )

    roadmap_steps = roadmap_result["roadmap_steps"]

    if not roadmap_steps:
        raise ValueError("roadmap_result contains no roadmap steps.")

    initial_match_esco = (roadmap_result["initial_match_esco"])
    final_match_esco = (roadmap_result["final_match_esco"])
    initial_match_esco_percent = (initial_match_esco * 100)
    final_match_esco_percent = (final_match_esco * 100)
    total_improvement_esco = (final_match_esco - initial_match_esco)
    total_improvement_esco_percent = (total_improvement_esco * 100)
    initial_match_market = (roadmap_result["initial_match_market"])
    final_match_market = (roadmap_result["final_match_market"])

    general_explanation = (
        f"The Personalized Career Skill Roadmap contains "
        f"{roadmap_result['roadmap_step_count']} sequential "
        f"skill-acquisition steps. "
        f"At each step, the remaining candidate skills are "
        f"re-evaluated and the skill with the highest current "
        f"ImprovementESCO is selected. "
        f"The roadmap therefore uses a greedy sequential "
        f"strategy with recalculated marginal improvements, "
        f"rather than copying a static initial skill ranking."
    )

    explained_steps = []

    for step in roadmap_steps:
        required_step_fields = {
            "step",
            "skill_id",
            "skill_name",
            "relation_type",
            "coverage_before",
            "residual_gap_before",
            "match_esco_before",
            "match_esco_after",
            "marginal_improvement_esco",
            "direct_improvement",
            "semantic_spillover",
            "semantic_dependency_ratio",
            "match_market_before",
            "match_market_after",
            "marginal_improvement_market",
            "rca",
            "market_gap_severity",
            "affected_esco_skill_count",
            "affected_esco_skills",
            "affected_market_skills",
            "selection_reason"
        }

        missing_step_fields = (required_step_fields - set(step.keys()))

        if missing_step_fields:
            raise ValueError("Roadmap step is missing required fields: "
                f"{sorted(missing_step_fields)}"
            )

        coverage_before_percent = (step["coverage_before"] * 100)
        residual_gap_percent = (step["residual_gap_before"] * 100)
        match_esco_before_percent = (step["match_esco_before"] * 100)
        match_esco_after_percent = (step["match_esco_after"] * 100)
        marginal_improvement_esco_percent = (step["marginal_improvement_esco"] * 100)
        direct_improvement_percent = (step["direct_improvement"] * 100)
        semantic_spillover_percent = (step["semantic_spillover"] * 100)
        semantic_dependency_percent = (step["semantic_dependency_ratio"] * 100)

        core_explanation = (
            f"At roadmap step {step['step']}, "
            f"'{step['skill_name']}' is selected. The skill is classified as "
            f"'{step['relation_type']}' in the canonical "
            f"ESCO profile. Before acquisition, its current coverage is "
            f"{coverage_before_percent:.2f}% and its residual "
            f"gap is {residual_gap_percent:.2f}%."
        )

        improvement_explanation = (
            f"Simulating the acquisition of "
            f"'{step['skill_name']}' increases MatchESCO "
            f"from {match_esco_before_percent:.2f}% to "
            f"{match_esco_after_percent:.2f}%, corresponding to a marginal improvement of "
            f"{marginal_improvement_esco_percent:.2f} percentage points. "
            f"{direct_improvement_percent:.2f} percentage points come from direct coverage, while "
            f"{semantic_spillover_percent:.2f} percentage points come from semantic spillover."
        )

        semantic_explanation = (
            f"The semantic dependency ratio for this step is "
            f"{semantic_dependency_percent:.2f}%. The simulated acquisition affects "
            f"{step['affected_esco_skill_count']} canonical ESCO skill entries in total."
        )

        if step["marginal_improvement_market"] is None:
            market_explanation = ("No MatchMarket improvement is available for this roadmap step.")
            market_available = False
            marginal_improvement_market_percent = None
        else:
            marginal_improvement_market_percent = (step["marginal_improvement_market"] * 100)

            if step["marginal_improvement_market"] == 0.0:
                market_explanation = (
                    "Market-based evaluation is available, but this simulated skill acquisition produces no measured MatchMarket improvement under the current model."
                )
            else:
                market_explanation = (
                    f"The estimated MatchMarket improvement for this step is "
                    f"{marginal_improvement_market_percent:.2f} percentage points. This value is supplementary and does not determine the roadmap ordering."
                )

            market_available = True

        explanation_text = " ".join([
            core_explanation,
            improvement_explanation,
            semantic_explanation,
            market_explanation
        ])

        explained_steps.append({
            "step": step["step"],
            "skill_id": step["skill_id"],
            "skill_name": step["skill_name"],
            "relation_type": step["relation_type"],
            "coverage_before": step["coverage_before"],
            "coverage_before_percent": coverage_before_percent,
            "residual_gap_before": step["residual_gap_before"],
            "residual_gap_percent": residual_gap_percent,
            "match_esco_before": step["match_esco_before"],
            "match_esco_before_percent": match_esco_before_percent,
            "match_esco_after": step["match_esco_after"],
            "match_esco_after_percent": match_esco_after_percent,
            "marginal_improvement_esco": step["marginal_improvement_esco"],
            "marginal_improvement_esco_percent": marginal_improvement_esco_percent,
            "direct_improvement": step["direct_improvement"],
            "direct_improvement_percent": direct_improvement_percent,
            "semantic_spillover": step["semantic_spillover"],
            "semantic_spillover_percent": semantic_spillover_percent,
            "semantic_dependency_ratio": step["semantic_dependency_ratio"],
            "semantic_dependency_percent": semantic_dependency_percent,
            "affected_esco_skill_count": step["affected_esco_skill_count"],
            "affected_esco_skills": step["affected_esco_skills"],
            "market_available": market_available,
            "marginal_improvement_market": step["marginal_improvement_market"],
            "marginal_improvement_market_percent": marginal_improvement_market_percent,
            "rca": step["rca"],
            "market_gap_severity": step["market_gap_severity"],
            "affected_market_skills": step["affected_market_skills"],
            "selection_reason": step["selection_reason"],
            "core_explanation": core_explanation,
            "improvement_explanation": improvement_explanation,
            "semantic_explanation": semantic_explanation,
            "market_explanation": market_explanation,
            "explanation_text": explanation_text
        })

    impact_explanation = (
        f"Across the complete simulated roadmap, MatchESCO increases from "
        f"{initial_match_esco_percent:.2f}% to "
        f"{final_match_esco_percent:.2f}%, for a total increase of "
        f"{total_improvement_esco_percent:.2f} percentage points. After the generated steps, "
        f"{roadmap_result['remaining_candidate_skill_count']} candidate skill gaps remain for possible later roadmap steps."
    )

    return {
        "explanation_type": "career_skill_roadmap",
        "occupation_id": roadmap_result["occupation_id"],
        "selection_method": roadmap_result["selection_method"],
        "selection_strategy": roadmap_result["selection_strategy"],
        "roadmap_step_count": roadmap_result["roadmap_step_count"],
        "initial_match_esco": initial_match_esco,
        "initial_match_esco_percent": initial_match_esco_percent,
        "final_match_esco": final_match_esco,
        "final_match_esco_percent": final_match_esco_percent,
        "total_improvement_esco": total_improvement_esco,
        "total_improvement_esco_percent": total_improvement_esco_percent,
        "initial_match_market": initial_match_market,
        "final_match_market": final_match_market,
        "remaining_candidate_skill_count": roadmap_result["remaining_candidate_skill_count"],
        "general_explanation": general_explanation,
        "impact_explanation": impact_explanation,
        "roadmap_steps": explained_steps,
        "explanation_text":
            (general_explanation + " " + impact_explanation)
    }