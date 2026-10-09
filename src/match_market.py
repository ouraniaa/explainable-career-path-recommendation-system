"""
Calculates the supplementary labor-market match for a user and an occupation.

This module was created because the main MatchESCO score only reflects official ESCO
requirements and does not show whether those requirements are also supported by the
available job-posting data. To keep the two evidence sources separate, MatchMarket uses
only occupation-skill pairs that appear in BOTH ESCO and the market profile.

Each eligible skill is weighted by its occupation-specific RCA value and multiplied by
the user's existing coverage for that skill. The final score is a market-weighted
coverage measure, not a direct measure of job demand, and it is kept separate from the
main ESCO ranking.
"""
import numpy as np
import pandas as pd

from src.match_esco import calculate_skill_coverage

PROFILE_FILE = ("data/processed/occupation_skill_profiles.csv")

MIN_BOTH_SKILLS = 5

PROFILES_DF = pd.read_csv(PROFILE_FILE)

def calculate_match_market(occupation_id, user_skill_ids, coverage_lookup=None):
    """
    RCA-weighted Market Match.

    Only occupation-skill pairs with source_type == BOTH are included.

    Returns N/A when:
    - fewer than 5 BOTH skills are available
    - RCA values are invalid
    - total RCA weight is zero
    """
    occupation_df = PROFILES_DF[
        (PROFILES_DF["occupation_id"] == occupation_id) &
        (PROFILES_DF["source_type"] == "BOTH")
    ].copy()

    both_skill_count = len(occupation_df)

    if both_skill_count < MIN_BOTH_SKILLS:
        return {
            "occupation_id": occupation_id,
            "match_market": None,
            "both_skill_count": both_skill_count,
            "reason": "Insufficient BOTH skills",
            "details": []
        }

    if occupation_df["skill_id"].duplicated().any():

        raise ValueError(
            "Duplicate occupation-skill pairs detected "
            f"for occupation {occupation_id}."
        )

    rca_values = pd.to_numeric(occupation_df["rca"], errors="coerce")

    invalid_rca = (rca_values.isna().any() or not np.isfinite(rca_values).all() or (rca_values <= 0).any())

    if invalid_rca:
        return {
            "occupation_id": occupation_id,
            "match_market": None,
            "both_skill_count": both_skill_count,
            "reason": "Invalid RCA values",
            "details": []
        }

    occupation_df["rca"] = rca_values

    user_skill_ids = set(user_skill_ids)

    weighted_coverage_sum = 0.0
    total_rca = 0.0
    details = []

    for _, row in occupation_df.iterrows():

        skill_id = row["skill_id"]
        skill_name = row["skill_name"]
        rca = float(row["rca"])

        if (coverage_lookup is not None and skill_id in coverage_lookup):
            coverage = coverage_lookup[skill_id]
        else:
            coverage = calculate_skill_coverage(required_skill_id=skill_id, user_skill_ids=user_skill_ids)

        weighted_coverage = (rca * coverage)
        weighted_coverage_sum += weighted_coverage
        total_rca += rca

        details.append({
            "skill_id": skill_id,
            "skill_name": skill_name,
            "rca": rca,
            "coverage": coverage,
            "weighted_coverage": weighted_coverage
        })

    if total_rca <= 0 or not np.isfinite(total_rca):
        return {
            "occupation_id": occupation_id,
            "match_market": None,
            "both_skill_count": both_skill_count,
            "reason": "Invalid total RCA",
            "details": details
        }

    match_market = (weighted_coverage_sum / total_rca)

    details.sort(key=lambda x: x["rca"], reverse=True)

    return {
        "occupation_id": occupation_id,
        "match_market": match_market,
        "both_skill_count": both_skill_count,
        "total_rca": total_rca,
        "weighted_coverage_sum": weighted_coverage_sum,
        "details": details
    }