"""
Ranks candidate skills by their estimated improvement to the user's ESCO match.

This module was created to turn the raw skill-gap analysis into a more useful learning
order. Instead of treating every missing or partially covered skill as equally important,
it simulates the effect of adding each candidate skill and measures how much the main
MatchESCO score would improve.

The result is a learning-priority list based only on estimated ESCO improvement. It does
not mix market evidence or graph similarity into the ranking, which keeps the recommendation
logic transparent and consistent with the methodology.
"""
from src.recommendation_engine import recommend_occupation
from src.match_improvement import (calculate_match_improvement, calculate_market_improvement)

def calculate_learning_priority(session, occupation_id, user_skill_ids, top_n=None):
    if top_n is not None:
        if (type(top_n) is not int or top_n <= 0):
            raise ValueError("top_n must be a positive integer or None.")

    recommendation = recommend_occupation(session=session, occupation_id=occupation_id, user_skill_ids=user_skill_ids)
    skill_gaps = (recommendation["skill_gaps"])
    market_details = (recommendation["market_details"])
    market_lookup = {
        item["skill_id"]: item
        for item in market_details
    }


    user_skill_set = set(user_skill_ids)

    candidate_skills = [
        item
        for item in skill_gaps
        if item["gap"] > 0.0
        and item["skill_id"]
        not in user_skill_set
    ]


    ranked_skills = []

    for candidate in candidate_skills:
        skill_id = candidate["skill_id"]
        esco_result = (calculate_match_improvement(skill_gaps=skill_gaps, new_skill_id=skill_id))
        current_coverage = float(candidate["coverage"])
        direct_improvement = (1.0 - current_coverage) / recommendation["canonical_skill_count"]
        semantic_spillover = (esco_result["improvement_esco"] - direct_improvement)
        semantic_spillover = max(0.0, semantic_spillover)

        if (esco_result["improvement_esco"] > 0.0):
            semantic_dependency_ratio = (semantic_spillover / esco_result["improvement_esco"])
        else:
            semantic_dependency_ratio = 0.0

        market_result = (calculate_market_improvement(market_details= market_details, improvement_result= esco_result))

        market_evidence = (market_lookup.get(skill_id))

        if market_evidence is not None:
            rca = float(market_evidence["rca"])

            market_gap_severity = (rca * candidate["gap"])
        else:
            rca = None
            market_gap_severity = None

        ranked_skills.append({
            "skill_id": skill_id,
            "skill_name": candidate["skill_name"],
            "relation_type": candidate["relation_type"],
            "match_type": candidate["match_type"],
            "current_coverage": candidate["coverage"],
            "residual_gap": candidate["gap"],           
            "improvement_esco": esco_result["improvement_esco"],
            "direct_improvement": direct_improvement,
            "semantic_spillover": semantic_spillover,
            "semantic_dependency_ratio": semantic_dependency_ratio,
            "rca": rca,
            "market_gap_severity": market_gap_severity,
            "improvement_market": market_result["improvement_market"],
            "affected_esco_skill_count": esco_result["affected_skill_count"],
            "affected_esco_skills": esco_result["affected_skills"],
            "affected_market_skills": market_result["affected_market_skills"]
        })

    ranked_skills.sort(
        key=lambda item: (
            -item["improvement_esco"],
            item["skill_name"].lower(),
            item["skill_id"]
        )
    )

    for index, item in enumerate(ranked_skills, start=1):
        item["rank"] = index

    total_candidates = len(ranked_skills)

    if top_n is not None:
        ranked_skills = (ranked_skills[:top_n])

    return {
        "occupation_id": occupation_id,
        "current_match_esco": recommendation["match_esco"],
        "current_match_market": recommendation["match_market"],
        "canonical_skill_count": recommendation["canonical_skill_count"],
        "total_candidate_skills": total_candidates,
        "ranking_criterion": "improvement_esco",
        "ranked_skills": ranked_skills
    }