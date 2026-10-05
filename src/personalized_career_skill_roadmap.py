"""
Builds a personalized step-by-step skill learning roadmap for a target occupation.

A simple ranked list of useful skills is not enough to show how the user's profile could 
improve over time. The roadmap therefore applies a greedy sequential process: at each
step it selects the skill with the highest current estimated ImprovementESCO, adds it 
to the simulated user profile, and recalculates the remaining priorities before choosing 
the next step.

This makes the roadmap adaptive to the user's evolving simulated profile.
"""
from src.learning_priority import (calculate_learning_priority)
from src.recommendation_engine import (recommend_occupation)

def generate_personalized_career_skill_roadmap(session, occupation_id, user_skill_ids, max_steps=5):
    """
    Process:
    1. The Learning Priority Ranking is recalculated
       using the current simulated user profile.
    2. The skill with the highest current
       ImprovementESCO is selected.
    3. The selected skill is temporarily added
       to the simulated user profile.
    4. The matching state is recalculated.
    """
    if (type(max_steps) is not int or max_steps <= 0):
        raise ValueError("max_steps must be a positive integer.")

    if not occupation_id:
        raise ValueError("occupation_id cannot be empty.")

    current_user_skill_ids = list(dict.fromkeys(user_skill_ids))
    initial_user_skill_ids = list(current_user_skill_ids)

    roadmap_steps = []

    initial_result = recommend_occupation(session=session, occupation_id=occupation_id, user_skill_ids=current_user_skill_ids)

    initial_match_esco = (initial_result["match_esco"])
    initial_match_market = (initial_result["match_market"])

    for step_number in range(1, max_steps + 1):
        priority_result = (
            calculate_learning_priority(
                session=session,
                occupation_id=occupation_id,
                user_skill_ids=current_user_skill_ids,
                top_n=1
            )
        )

        ranked_skills = (priority_result["ranked_skills"])

        if not ranked_skills:
            break

        selected_skill = (ranked_skills[0])
        current_match_esco = (priority_result["current_match_esco"])
        current_match_market = (priority_result["current_match_market"])
        updated_user_skill_ids = (current_user_skill_ids + [selected_skill["skill_id"]])

        updated_result = recommend_occupation(
            session=session,
            occupation_id=occupation_id,
            user_skill_ids=updated_user_skill_ids
        )

        updated_match_esco = (updated_result["match_esco"])
        updated_match_market = (updated_result["match_market"])

        actual_esco_improvement = (updated_match_esco - current_match_esco)
        expected_esco_improvement = (selected_skill["improvement_esco"])

        if abs(actual_esco_improvement - expected_esco_improvement) > 1e-10:
            raise ValueError("Roadmap ImprovementESCO does not match the full MatchESCO recalculation.")

        roadmap_steps.append({ 
            "step": step_number,
            "skill_id": selected_skill["skill_id"],
            "skill_name": selected_skill["skill_name"],
            "relation_type": selected_skill["relation_type"],
            "coverage_before": selected_skill["current_coverage"],
            "residual_gap_before": selected_skill["residual_gap"],
            "match_esco_before": current_match_esco,
            "match_esco_after": updated_match_esco,
            "marginal_improvement_esco": expected_esco_improvement,
            "direct_improvement": selected_skill["direct_improvement"],
            "semantic_spillover": selected_skill["semantic_spillover"],
            "semantic_dependency_ratio": selected_skill["semantic_dependency_ratio"],
            "match_market_before": current_match_market,
            "match_market_after": updated_match_market, 
            "marginal_improvement_market": selected_skill["improvement_market"],
            "rca": selected_skill["rca"],
            "market_gap_severity": selected_skill["market_gap_severity"],
            "affected_esco_skill_count": selected_skill["affected_esco_skill_count"],
            "affected_esco_skills": selected_skill["affected_esco_skills"],
            "affected_market_skills": selected_skill["affected_market_skills"],
            "selection_reason":
                (
                    "Selected because it has the highest "
                    "current ImprovementESCO among the "
                    "remaining canonical skill gaps."
                )
        })

        current_user_skill_ids = (updated_user_skill_ids)

    final_result = recommend_occupation(session=session, occupation_id=occupation_id, user_skill_ids=current_user_skill_ids)

    final_priority_result = (
        calculate_learning_priority(session=session, occupation_id=occupation_id, user_skill_ids=current_user_skill_ids)
    )

    return {
        "occupation_id": occupation_id,
        "selection_method": "sequential_marginal_improvement_esco",
        "selection_strategy": "greedy",
        "initial_user_skill_count": len(initial_user_skill_ids),
        "initial_match_esco": initial_match_esco,
        "initial_match_market": initial_match_market,
        "requested_max_steps": max_steps,
        "roadmap_step_count": len(roadmap_steps),
        "roadmap_steps": roadmap_steps,
        "final_simulated_skill_count": len(current_user_skill_ids),
        "final_match_esco": final_result["match_esco"],
        "final_match_market": final_result["match_market"],
        "remaining_candidate_skill_count": final_priority_result["total_candidate_skills"]
    }