"""
Estimates how much learning a new skill could improve the user's ESCO match.

This module was created because identifying missing skills alone does not show which
one would make the biggest difference to the user's target occupation. To support
learning-priority and roadmap decisions, the file simulates adding one candidate skill
to the user's current profile and recalculates the resulting MatchESCO score.

The improvement value is purely ESCO-based. Market evidence and graph similarity are
kept separate so the result remains easy to interpret.
"""
import math
import numpy as np

from src.match_esco import (EMBEDDING_LOOKUP, SEMANTIC_THRESHOLD)

def calculate_match_improvement(skill_gaps, new_skill_id):
    """
    Calculates how much MatchESCO would improve if the user acquired one additional skill.
    ImprovementESCO(s) = MatchESCO(U union {s}, o) - MatchESCO(U, o)

    Uses:
    - existing skill coverage values
    - precomputed skill embeddings
    """
    if not skill_gaps:
        raise ValueError("skill_gaps cannot be empty.")

    if not new_skill_id:
        raise ValueError("new_skill_id cannot be empty.")

    if new_skill_id not in EMBEDDING_LOOKUP:
        raise ValueError(f"No cached embedding for skill: {new_skill_id}")

    canonical_skill_count = len(skill_gaps)

    new_embedding = EMBEDDING_LOOKUP[new_skill_id]

    total_coverage_increase = 0.0

    affected_skills = []

    seen_skill_ids = set()

    for item in skill_gaps:
        required_skill_id = item["skill_id"]
        required_skill_name = item["skill_name"]
        old_coverage = float(item["coverage"])

        if (not math.isfinite(old_coverage) or old_coverage < 0.0 or old_coverage > 1.0):
            raise ValueError(f"Invalid coverage: {old_coverage}")

        if required_skill_id in seen_skill_ids:
            raise ValueError(
                f"Duplicate canonical skill: "
                f"{required_skill_id}"
            )

        seen_skill_ids.add(required_skill_id)

        if required_skill_id == new_skill_id:
            potential_coverage = 1.0
        else:
            required_embedding = EMBEDDING_LOOKUP.get(required_skill_id)
            if required_embedding is None:
                potential_coverage = 0.0
            else:
                similarity = float(np.dot(required_embedding, new_embedding))

                if similarity >= SEMANTIC_THRESHOLD:
                    potential_coverage = min(1.0, max(0.0, similarity))
                else:
                    potential_coverage = 0.0

        new_coverage = max(old_coverage, potential_coverage)
        coverage_increase = (new_coverage - old_coverage)
        total_coverage_increase += (coverage_increase)

        if coverage_increase > 1e-10:
            affected_skills.append({
                "skill_id": required_skill_id,
                "skill_name": required_skill_name,
                "relation_type": item.get("relation_type"),
                "old_coverage": old_coverage,
                "new_coverage": new_coverage,
                "coverage_increase": coverage_increase
            })

    improvement_esco = (total_coverage_increase / canonical_skill_count)

    affected_skills.sort(
        key=lambda item: (
            -item["coverage_increase"],
            item["skill_name"].lower()
        )
    )

    return {
        "new_skill_id": new_skill_id,
        "canonical_skill_count": canonical_skill_count,
        "improvement_esco": improvement_esco,
        "affected_skill_count": len(affected_skills),
        "affected_skills": affected_skills
    }

def calculate_market_improvement(market_details, improvement_result):
    """
    Calculates the MatchMarket improvement using previously calculated skill coverage increases.
    ImprovementMarket(s) = sum(RCA(r) * CoverageIncrease(r)) / sum(RCA(r))
    Only BOTH skills participate.
    """
    if not market_details:
        return {
            "improvement_market": None,
            "reason": "MatchMarket unavailable",
            "affected_market_skill_count": 0,
            "affected_market_skills": []
        }

    coverage_increases = {
        item["skill_id"]: item["coverage_increase"]
        for item in improvement_result["affected_skills"]
    }

    total_rca = 0.0
    weighted_increase_sum = 0.0

    affected_market_skills = []

    seen_skill_ids = set()

    for item in market_details:
        skill_id = item["skill_id"]
        skill_name = item["skill_name"]
        rca = float(item["rca"])

        if skill_id in seen_skill_ids:
            raise ValueError(f"Duplicate BOTH skill: {skill_id}")

        seen_skill_ids.add(skill_id)

        if not math.isfinite(rca) or rca <= 0.0:
            raise ValueError(f"Invalid RCA for skill {skill_id}: {rca}")

        coverage_increase = coverage_increases.get(skill_id, 0.0)

        weighted_increase = (rca * coverage_increase)

        total_rca += rca

        weighted_increase_sum += weighted_increase

        if coverage_increase > 1e-10:
            affected_market_skills.append({
                "skill_id": skill_id,
                "skill_name": skill_name,
                "rca": rca,
                "coverage_increase": coverage_increase,
                "weighted_increase": weighted_increase
            })

    if total_rca <= 0.0:
        return {
            "improvement_market": None,
            "reason": "Invalid total RCA",
            "affected_market_skill_count": 0,
            "affected_market_skills": []
        }

    improvement_market = (weighted_increase_sum / total_rca)

    affected_market_skills.sort(
        key=lambda item: (
            -item["weighted_increase"],
            item["skill_name"].lower()
        )
    )

    return {
        "improvement_market": improvement_market,
        "reason": None,
        "total_rca": total_rca,
        "weighted_increase_sum": weighted_increase_sum,
        "affected_market_skill_count": len(
            affected_market_skills
        ),
        "affected_market_skills": affected_market_skills
    }