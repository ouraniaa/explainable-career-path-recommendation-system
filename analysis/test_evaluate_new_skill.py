import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.recommendation_engine import (recommend_occupation, evaluate_new_skill)


TARGET_OCCUPATION_ID = ("258e46f9-0075-4a2e-adae-1ff0477e0f30")

USER_SKILL_IDS = [
    "5f0082ab-2131-49b5-94d6-a1821daf57d6",
    "505e4ef3-7ce4-437d-b7b4-5c608f71c258",
    "25f0ea33-b4a2-4f31-b7b4-7d20e827b180"
]


#1. Find Hadoop in the current recommendation
recommendation = recommend_occupation(
    occupation_id=TARGET_OCCUPATION_ID,
    user_skill_ids=USER_SKILL_IDS
)

hadoop = next(
    item
    for item in recommendation["skill_gaps"]
    if item["skill_name"].lower() == "hadoop"
)

new_skill_id = hadoop["skill_id"]


#2. Evaluate hypothetical acquisition
result = evaluate_new_skill(
    occupation_id=TARGET_OCCUPATION_ID,
    user_skill_ids=USER_SKILL_IDS,
    new_skill_id=new_skill_id
)


print("=" * 80)
print("EVALUATE NEW SKILL INTEGRATION TEST")
print("=" * 80)

print("New skill:", hadoop["skill_name"])
print(
    "ESCO:",
    f"{result['current_match_esco'] * 100:.4f}%",
    "->",
    f"{result['new_match_esco'] * 100:.4f}%"
)

print(
    "ESCO Improvement:",
    f"{result['improvement_esco'] * 100:.4f} percentage points"
)

print(
    "Market:",
    f"{result['current_match_market'] * 100:.4f}%",
    "->",
    f"{result['new_match_market'] * 100:.4f}%"
)

print(
    "Market Improvement:",
    f"{result['improvement_market'] * 100:.4f} percentage points"
)


#3. Verify against full recalculation
updated_user_skills = USER_SKILL_IDS + [new_skill_id]

updated_recommendation = recommend_occupation(
    occupation_id=TARGET_OCCUPATION_ID,
    user_skill_ids=updated_user_skills
)

assert abs(
    result["new_match_esco"]
    - updated_recommendation["match_esco"]
) < 1e-4

assert abs(
    result["new_match_market"]
    - updated_recommendation["match_market"]
) < 1e-4

#The hypothetical evaluation must not change the input list.
assert new_skill_id not in USER_SKILL_IDS

print("\nEVALUATE NEW SKILL INTEGRATION TEST PASSED")