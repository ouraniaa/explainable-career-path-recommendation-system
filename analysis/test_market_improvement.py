import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.recommendation_engine import recommend_occupation

from src.match_improvement import (calculate_match_improvement, calculate_market_improvement)

TARGET_OCCUPATION_ID = ("258e46f9-0075-4a2e-adae-1ff0477e0f30")

USER_SKILL_IDS = [
    "5f0082ab-2131-49b5-94d6-a1821daf57d6",
    "505e4ef3-7ce4-437d-b7b4-5c608f71c258",
    "25f0ea33-b4a2-4f31-b7b4-7d20e827b180"
]


#1. GET CURRENT RECOMMENDATION
recommendation = recommend_occupation(
    occupation_id=TARGET_OCCUPATION_ID,
    user_skill_ids=USER_SKILL_IDS
)

assert recommendation["match_market"] is not None

skill_gaps = recommendation["skill_gaps"]
market_details = recommendation["market_details"]


#2. SELECT HADOOP
hadoop = next(
    item
    for item in skill_gaps
    if item["skill_name"].lower() == "hadoop"
)

new_skill_id = hadoop["skill_id"]

#3. CALCULATE ESCO IMPROVEMENT
esco_improvement = calculate_match_improvement(skill_gaps=skill_gaps, new_skill_id=new_skill_id)


#4. CALCULATE MARKET IMPROVEMENT
market_improvement = calculate_market_improvement(market_details=market_details, improvement_result=esco_improvement)

print("=" * 80)
print("MARKET IMPROVEMENT TEST")
print("=" * 80)

print("New skill:", hadoop["skill_name"])

print(
    "Original MatchMarket:",
    f"{recommendation['match_market'] * 100:.4f}%"
)
print(
    "ESCO improvement:",
    f"{esco_improvement['improvement_esco'] * 100:.4f} "
    "percentage points"
)
print(
    "Market improvement:",
    f"{market_improvement['improvement_market'] * 100:.4f} "
    "percentage points"
)
print(
    "Affected market skills:",
    market_improvement["affected_market_skill_count"]
)

#5. VERIFY AGAINST FULL RECALCULATION
updated_user_skills = (USER_SKILL_IDS + [new_skill_id])

updated_recommendation = recommend_occupation(
    occupation_id=TARGET_OCCUPATION_ID,
    user_skill_ids=updated_user_skills
)

actual_market_improvement = (updated_recommendation["match_market"] - recommendation["match_market"])

predicted_market_improvement = (market_improvement["improvement_market"])

print(
    "Predicted Market Improvement:",
    f"{predicted_market_improvement * 100:.4f} "
    "percentage points"
)

print(
    "Actual Market Improvement:",
    f"{actual_market_improvement * 100:.4f} "
    "percentage points"
)

assert abs(actual_market_improvement - predicted_market_improvement) < 1e-4
assert market_improvement["improvement_market"] >= 0.0
assert (recommendation["match_market"] + market_improvement["improvement_market"] <= 1.00001)

print("\nMARKET IMPROVEMENT TEST PASSED")


#6. SHOW AFFECTED MARKET SKILLS
print("\n" + "=" * 80)
print("AFFECTED MARKET SKILLS")
print("=" * 80)

for item in market_improvement["affected_market_skills"]:
    print("Skill:", item["skill_name"])
    print(
        "RCA:",
        f"{item['rca']:.4f}"
    )
    print(
        "Coverage increase:",
        f"{item['coverage_increase']:.4f}"
    )
    print(
        "Weighted increase:",
        f"{item['weighted_increase']:.4f}"
    )
    print("-" * 80)

#TEST 2 — UNAVAILABLE MARKET MATCH
software_developer_id = "f2b15a0e-e65a-438a-affb-29b9d50b77d1"

software_result = recommend_occupation(occupation_id=software_developer_id, user_skill_ids=USER_SKILL_IDS)

assert software_result["match_market"] is None
assert software_result["market_details"] == []

unavailable_result = calculate_market_improvement(market_details=software_result["market_details"], improvement_result=esco_improvement)

assert unavailable_result["improvement_market"] is None
assert unavailable_result["reason"] == "MatchMarket unavailable"

print("\nUNAVAILABLE MARKET IMPROVEMENT TEST PASSED")