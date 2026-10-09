from src.recommendation_engine import (recommend_occupation)
from src.learning_priority import (calculate_learning_priority)
from src.personalized_skill_recommendation import (generate_personalized_skill_recommendations)
from src.personalized_career_skill_roadmap import (generate_personalized_career_skill_roadmap)
from src.explainability.job_match_explanation import (generate_job_match_explanation)
from src.explainability.skill_gap_explanation import (generate_skill_gap_explanation)
from src.explainability.overall_explanation import (generate_overall_explanation)
from src.career_transition_recommendation import (generate_career_transition_recommendations, generate_career_discovery_recommendations)
from src.explainability.career_path_explanation import (generate_career_skill_roadmap_explanation, generate_career_transition_explanation, generate_career_discovery_explanation,
    generate_career_path_comparison_explanation)
"""
Application service for the main career analysis workflows.

This file acts as the bridge between the API layer and the individual recommendation,
roadmap, and explainability modules. It does not calculate new scores itself. Instead,
it coordinates the existing components and combines their outputs into the structured
responses used by the frontend.
"""
def analyze_target_occupation(
    session,
    occupation_id,
    occupation_name,
    user_skill_ids,
    learning_priority_top_n=5,
    graph_top_n=3,
    roadmap_max_steps=5
):
    """
    Builds the complete analysis for a user-selected target occupation.

    The function coordinates the occupation match, learning priorities, personalized
    skill suggestions, career roadmap, and the corresponding explanations. Its role is
    orchestration only; the actual scoring and recommendation logic remains inside the
    specialized modules.
    """
    if not occupation_id:
        raise ValueError("occupation_id is required.")

    if not occupation_name:
        raise ValueError("occupation_name is required.")

    if not user_skill_ids:
        raise ValueError("user_skill_ids must contain at least one skill.")

    if learning_priority_top_n <= 0:
        raise ValueError("learning_priority_top_n must be positive.")

    if graph_top_n <= 0:
        raise ValueError("graph_top_n must be positive.")

    if roadmap_max_steps <= 0:
        raise ValueError("roadmap_max_steps must be positive.")

    #Starts with the main ESCO-based occupation match and skill-gap analysis.
    recommendation = recommend_occupation(
        session=session,
        occupation_id=occupation_id,
        user_skill_ids=user_skill_ids
    )

    #Ranks the missing or partially covered skills by their estimated ESCO improvement.
    learning_priority = (
        calculate_learning_priority(
            session=session,
            occupation_id=occupation_id,
            user_skill_ids=user_skill_ids,
            top_n=learning_priority_top_n
        )
    )

    #Enriches the learning priorities with personalized graph-based skill context.
    personalized_skills = (
        generate_personalized_skill_recommendations(
            session=session,
            occupation_id=occupation_id,
            user_skill_ids=user_skill_ids,
            top_n=learning_priority_top_n,
            graph_top_n=graph_top_n
        )
    )

    #Builds a step-by-step learning roadmap, recalculating the profile after each step.
    roadmap = (
        generate_personalized_career_skill_roadmap(
            session=session,
            occupation_id=occupation_id,
            user_skill_ids=user_skill_ids,
            max_steps=roadmap_max_steps
        )
    )


    #Converts the analytical results into deterministic, user-facing explanations.
    job_match_explanation = (generate_job_match_explanation(occupation_name=occupation_name, recommendation_result=recommendation))

    #The highest-priority skill receives its own explanation when available.
    ranked_skills = (learning_priority.get("ranked_skills", []))

    if ranked_skills:
        top_skill_explanation = (generate_skill_gap_explanation(ranked_skill=ranked_skills[0]))
    else:
        top_skill_explanation = None

    roadmap_explanation = (generate_career_skill_roadmap_explanation(roadmap))

    overall_explanation = (
        generate_overall_explanation(job_match_explanation= job_match_explanation,
            skill_gap_explanation= top_skill_explanation,
            career_path_explanation= roadmap_explanation,
            graph_explanation=None
        )
    )

    return {
        "analysis_type": "target_occupation",
        "occupation": {
            "occupation_id": occupation_id,
            "occupation_name": occupation_name
        },

        "user_skill_count": len(user_skill_ids),
        "recommendation": recommendation,
        "learning_priority": learning_priority,
        "personalized_skill_recommendations": personalized_skills,
        "roadmap": roadmap,
        "explanations": {
            "job_match": job_match_explanation,
            "top_skill_gap": top_skill_explanation,
            "roadmap": roadmap_explanation,
            "overall": overall_explanation
        }
    }

def analyze_career_paths(
    session,
    user_skill_ids,
    current_occupation_id=None,
    structural_top_n=10,
    recommendation_top_n=5,
    min_shared_skills=1
):
    """
    Runs either Career Transition or Career Discovery, depending on whether the user
    provides a current occupation.
    With a current occupation, the workflow first searches structurally related careers
    and then evaluates them against the user's skills. Without one, it performs direct
    career discovery from the user's profile. The function only coordinates existing
    recommendation and explainability logic.
    """
    if not user_skill_ids:
        raise ValueError("user_skill_ids must contain at least one skill.")

    if structural_top_n <= 0:
        raise ValueError("structural_top_n must be positive.")

    if recommendation_top_n <= 0:
        raise ValueError("recommendation_top_n must be positive.")

    if min_shared_skills < 0:
        raise ValueError("min_shared_skills must be non-negative.")


    #A known current occupation activates the career-transition workflow.
    if current_occupation_id is not None:
        career_result = (
            generate_career_transition_recommendations(
                session=session,
                current_occupation_id=current_occupation_id,
                user_skill_ids=user_skill_ids,
                structural_top_n=structural_top_n,
                recommendation_top_n=recommendation_top_n,
                min_shared_skills=min_shared_skills
            )
        )

        career_explanation = (generate_career_transition_explanation(career_result))
        recommendations = career_result.get("recommendations", [])

        if len(recommendations) >= 2:
            comparison_explanation = generate_career_path_comparison_explanation(
                preferred_candidate=recommendations[0],
                alternative_candidate=recommendations[1]
            )
        else:
            comparison_explanation = None
        mode = "career_transition"

    else:
        #Without a current occupation, recommendations are generated directly from the profile.
        career_result = (
            generate_career_discovery_recommendations(
                session=session,
                user_skill_ids=user_skill_ids,
                recommendation_top_n=recommendation_top_n
            )
        )

        career_explanation = (generate_career_discovery_explanation(career_result))
        recommendations = career_result.get("recommendations", [])

        if len(recommendations) >= 2:
            comparison_explanation = generate_career_path_comparison_explanation(
                preferred_candidate=recommendations[0],
                alternative_candidate=recommendations[1]
            )
        else:
            comparison_explanation = None

        mode = "career_discovery"

    return {
        "analysis_type": "career_paths",
        "mode": mode,
        "current_occupation_id": current_occupation_id,
        "user_skill_count": len(user_skill_ids),
        "career_result": career_result,
        "explanation": career_explanation,
        "comparison_explanation": comparison_explanation
    }