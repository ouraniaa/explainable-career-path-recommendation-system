"""
Handles the two career-path recommendation workflows used by the application.

The module supports Career Transition when the user provides a current occupation,
and Career Discovery when they do not. Transition first uses structural occupation
similarity to generate related candidates and then evaluates those candidates with
the main ESCO-based recommendation logic. Discovery evaluates the analytical
occupation set directly from the user's selected skills.

The module coordinates existing scoring functions and prepares the result objects
used by the API and frontend; it does not introduce a new combined score.
"""
from pathlib import Path
import pandas as pd

from src.occupation_similarity import (find_similar_occupations)
from src.recommendation_engine import (recommend_occupation)

def generate_career_transition_recommendations(
    session,
    current_occupation_id,
    user_skill_ids,
    structural_top_n=10,
    recommendation_top_n=5,
    min_shared_skills=1
):
    """
    Generates user-specific career transition recommendations.
    Process:
    1. Find structurally related occupations using Jaccard similarity.
    2. Keep the top structural candidates.
    3. Evaluate each candidate against the user's
       current skill profile.
    4. Rank candidates by MatchESCO.

    Occupation Jaccard is used only for candidate
    generation / filtering.
    Final user-specific ranking criterion: MatchESCO

    MatchMarket and skill-gap information are returned
    as supplementary explanatory signals.
    """
    if not current_occupation_id:
        raise ValueError("current_occupation_id cannot be empty.")

    if (type(structural_top_n) is not int or structural_top_n <= 0):
        raise ValueError("structural_top_n must be a positive integer.")

    if (type(recommendation_top_n) is not int or recommendation_top_n <= 0):
        raise ValueError("recommendation_top_n must be a positive integer.")

    if (type(min_shared_skills) is not int or min_shared_skills < 0):
        raise ValueError("min_shared_skills must be a non-negative integer.")

    user_skill_ids = list(dict.fromkeys(user_skill_ids))

    structural_result = find_similar_occupations(
        session=session,
        current_occupation_id=current_occupation_id,
        top_n=structural_top_n,
        min_shared_skills=min_shared_skills
    )

    structural_candidates = (structural_result["similar_occupations"])

    evaluated_candidates = []

    for candidate in structural_candidates:
        recommendation = recommend_occupation(session=session, occupation_id=candidate["occupation_id"], user_skill_ids=user_skill_ids)

        evaluated_candidates.append({
            "occupation_id": candidate["occupation_id"],
            "occupation_name": candidate["occupation_name"],
            "isco_group": candidate["isco_group"],
            "structural_rank": candidate["rank"],
            "occupation_similarity": candidate["jaccard_similarity"],
            "shared_skill_count": candidate["shared_skill_count"],
            "union_skill_count": candidate["union_skill_count"],
            "candidate_skill_count": candidate["candidate_skill_count"],
            "match_esco": recommendation["match_esco"],
            "match_market": recommendation["match_market"],
            "market_reason": recommendation["market_reason"],
            "market_details": recommendation["market_details"],
            "canonical_skill_count": recommendation["canonical_skill_count"],
            "exact_match_count": recommendation["exact_match_count"],
            "semantic_match_count": recommendation["semantic_match_count"],
            "missing_skill_count": recommendation["missing_skill_count"],
            "average_gap": recommendation["average_gap"],
            "skill_gaps": recommendation["skill_gaps"]
        })

    evaluated_candidates.sort(
        key=lambda item: (
            -item["match_esco"],
            item["occupation_name"] or "",
            item["occupation_id"]
        )
    )

    final_candidates = (evaluated_candidates[:recommendation_top_n])

    ranked_recommendations = []

    for rank, item in enumerate(final_candidates, start=1):
        ranked_recommendations.append({
            "rank": rank,
            **item
        })

    return {
        "mode": "career_transition",
        "current_occupation_id": structural_result["current_occupation_id"],
        "current_occupation_name": structural_result["current_occupation_name"],
        "current_occupation_isco_group": structural_result["current_occupation_isco_group"],
        "candidate_pool_definition": structural_result["candidate_pool_definition"],
        "structural_similarity_method": structural_result["similarity_method"],
        "structural_filtering_role": "candidate_generation_only",
        "final_ranking_criterion": 
            "match_esco",
        "structural_top_n": structural_top_n,
        "recommendation_top_n": recommendation_top_n,
        "evaluated_candidate_count": len(evaluated_candidates),
        "recommendations": ranked_recommendations
    }


def get_discovery_candidate_occupations():
    """
    Returns the supported occupation pool used by
    Career Discovery.

    The pool is derived from the existing file "occupation_skill_profiles.csv".

    One record is returned per unique occupation_id.
    When duplicate rows exist, rows with a non-null ISCO group are preferred.

    No additional ranking is performed here.
    """
    project_root = (Path(__file__).resolve().parent.parent)
    profile_path = (project_root/ "data"/ "processed"/ "occupation_skill_profiles.csv")
    profiles = pd.read_csv(profile_path)

    required_columns = {
        "occupation_id",
        "occupation_name",
        "isco_group"
    }

    missing_columns = (required_columns - set(profiles.columns))

    if missing_columns:
        raise ValueError("occupation_skill_profiles.csv is missing "
            f"required columns: "
            f"{sorted(missing_columns)}"
        )

    occupations = (profiles[["occupation_id", "occupation_name", "isco_group"]].copy())

    occupations["has_isco_group"] = (occupations["isco_group"].notna())

    occupations = (occupations.sort_values(by=["occupation_id", "has_isco_group"], ascending=[True, False])
        .drop_duplicates(
            subset=["occupation_id"],
            keep="first"
        )
        .sort_values(
            by=["occupation_name", "occupation_id"]
        )
        .drop(
            columns=["has_isco_group"]
        )
    )

    occupations["isco_group"] = (
        occupations["isco_group"].apply(
            lambda value:
                str(int(value))
                if pd.notna(value)
                else None
        )
    )

    return occupations.to_dict(orient="records")


def generate_career_discovery_recommendations(session, user_skill_ids, recommendation_top_n=5):
    """
    Generates Career Discovery recommendations for
    users who do not provide a current occupation.

    Each supported analytical occupation is evaluated
    directly against the user's current skill profile.

    Final ranking criterion: MatchESCO
    """
    if (type(recommendation_top_n) is not int or recommendation_top_n <= 0):
        raise ValueError("recommendation_top_n must be a positive integer.")

    user_skill_ids = list(dict.fromkeys(user_skill_ids))

    if not user_skill_ids:
        raise ValueError("user_skill_ids cannot be empty.")


    candidate_occupations = (get_discovery_candidate_occupations())

    if not candidate_occupations:
        raise ValueError("No occupations are available for Career Discovery.")

    evaluated_candidates = []

    for candidate in candidate_occupations:
        recommendation = recommend_occupation(
            session=session,
            occupation_id=candidate["occupation_id"],
            user_skill_ids=user_skill_ids
        )

        evaluated_candidates.append({
            "occupation_id": candidate["occupation_id"],
            "occupation_name": candidate["occupation_name"],
            "isco_group": candidate["isco_group"],
            "match_esco": recommendation["match_esco"],
            "match_market": recommendation["match_market"],
            "market_reason": recommendation["market_reason"],
            "market_details": recommendation["market_details"],
            "canonical_skill_count": recommendation["canonical_skill_count"],
            "exact_match_count": recommendation["exact_match_count"],
            "semantic_match_count": recommendation["semantic_match_count"],
            "missing_skill_count": recommendation["missing_skill_count"],
            "average_gap": recommendation["average_gap"],
            "skill_gaps": recommendation["skill_gaps"]
        })

    evaluated_candidates.sort(
        key=lambda item: (
            -item["match_esco"],
            item["occupation_name"] or "",
            item["occupation_id"]
        )
    )

    final_candidates = (evaluated_candidates[:recommendation_top_n])

    ranked_recommendations = []

    for rank, item in enumerate(final_candidates, start=1):
        ranked_recommendations.append({
            "rank": rank,
            **item
        })

    return {
        "mode": "career_discovery",
        "candidate_pool": "analytical_occupation_profile",
        "candidate_count": len(candidate_occupations),
        "final_ranking_criterion": "match_esco",
        "recommendation_top_n": recommendation_top_n,
        "recommendations": ranked_recommendations
    }