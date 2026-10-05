"""
Main recommendation layer for evaluating a user against one occupation.

This file was created to keep the main pieces of the analysis in one place instead of
repeating the same sequence across Target Occupation, Career Transition, and Career
Discovery. It combines the ESCO match, the supplementary market match, and the skill-gap
analysis into one consistent result object that the higher-level workflows can reuse.

The function also receives an existing Neo4j session from the caller. This became
important when multiple occupations had to be evaluated in Career Discovery, because
reopening database connections for every occupation caused unnecessary performance
overhead. Reusing the same session keeps the calculation much faster without changing
the scoring logic.
"""
from src.match_esco import calculate_match_esco
from src.match_market import calculate_match_market
from src.skill_gap_analysis import calculate_skill_gaps
from src.match_improvement import (calculate_match_improvement,calculate_market_improvement)

def recommend_occupation(session, occupation_id, user_skill_ids):
    """
    This function coordinates the main ESCO match, the supplementary market evidence,
    and the skill-gap analysis, then returns them in one shared structure. It does not
    introduce a new combined score.
    """
    esco_result = calculate_match_esco(session=session, occupation_id=occupation_id, user_skill_ids=user_skill_ids)

    coverage_lookup = {
        detail["required_skill_id"]:
            detail["coverage"]
        for detail in esco_result["details"]
    }

    market_result = calculate_match_market(occupation_id=occupation_id, user_skill_ids=user_skill_ids, coverage_lookup=coverage_lookup)

    gap_result = calculate_skill_gaps(esco_result["details"])

    return {
        "occupation_id": occupation_id,
        "match_esco": esco_result["match_esco"],
        "canonical_skill_count": esco_result["canonical_skill_count"],
        "exact_match_count": esco_result["exact_match_count"],
        "semantic_match_count": esco_result["semantic_match_count"],

        "match_market":market_result["match_market"],
        "both_skill_count": market_result["both_skill_count"],
        "market_reason": market_result.get("reason"),

        "average_gap": gap_result["average_gap"],
        "missing_skill_count": gap_result["missing_count"],
        "skill_gaps": gap_result["skill_gaps"],

        "esco_details": esco_result["details"],
        "market_details": market_result["details"]
    }


def evaluate_new_skill(session, occupation_id, user_skill_ids, new_skill_id):
    """
    Estimate how the results would change if the user acquired one additional skill.

    The function starts from the current occupation recommendation and applies the
    existing ESCO and market improvement logic.
    """
    recommendation = recommend_occupation(session=session, occupation_id=occupation_id, user_skill_ids=user_skill_ids)
    esco_improvement = calculate_match_improvement(skill_gaps=recommendation["skill_gaps"], new_skill_id=new_skill_id)
    market_improvement = calculate_market_improvement(market_details=recommendation["market_details"],improvement_result=esco_improvement)
    new_match_esco = (recommendation["match_esco"] + esco_improvement["improvement_esco"])

    if recommendation["match_market"] is not None:
        new_match_market = (recommendation["match_market"] + market_improvement["improvement_market"])
    else:
        new_match_market = None

    return {
        "occupation_id": occupation_id,
        "new_skill_id": new_skill_id,
        "current_match_esco": recommendation["match_esco"],
        "current_match_market": recommendation["match_market"],
        "improvement_esco": esco_improvement["improvement_esco"],
        "improvement_market": market_improvement["improvement_market"],
        "new_match_esco": new_match_esco,
        "new_match_market": new_match_market,
        "affected_esco_skills": esco_improvement["affected_skills"], 
        "affected_market_skills": market_improvement["affected_market_skills"], 
        "market_reason": market_improvement.get("reason")
    }