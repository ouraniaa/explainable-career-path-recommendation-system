import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

sys.path.insert(0, str(PROJECT_ROOT))

from src.recommendation_engine import recommend_occupation
from src.match_improvement import calculate_match_improvement

TARGET_OCCUPATION_ID = ("258e46f9-0075-4a2e-adae-1ff0477e0f30")

#Use the same user skills as previous tests.
USER_SKILL_IDS = [
    "5f0082ab-2131-49b5-94d6-a1821daf57d6",
    "505e4ef3-7ce4-437d-b7b4-5c608f71c258",
    "25f0ea33-b4a2-4f31-b7b4-7d20e827b180"
]


#1. GET CURRENT RECOMMENDATION
recommendation = recommend_occupation(occupation_id=TARGET_OCCUPATION_ID, user_skill_ids=USER_SKILL_IDS)

skill_gaps = recommendation["skill_gaps"]


#2. SELECT A MISSING SKILL
# We select Hadoop dynamically by its name instead of hardcoding another ESCO UUID.

hadoop = next(
    item
    for item in skill_gaps
    if item["skill_name"].lower() == "hadoop"
)

NEW_SKILL_ID = hadoop["skill_id"]


#3. CALCULATE IMPROVEMENT

result = calculate_match_improvement(skill_gaps=skill_gaps, new_skill_id=NEW_SKILL_ID)


print("=" * 80)
print("MATCH IMPROVEMENT TEST")
print("=" * 80)

print("New skill:", hadoop["skill_name"])
print(
    "Original MatchESCO:",
    f"{recommendation['match_esco'] * 100:.2f}%"
)
print(
    "Improvement:",
    f"{result['improvement_esco'] * 100:.2f} percentage points"
)
print(
    "Estimated new MatchESCO:",
    f"{(recommendation['match_esco'] + result['improvement_esco']) * 100:.2f}%"
)
print("Affected skills:", result["affected_skill_count"])


assert result["canonical_skill_count"] == 97
assert result["improvement_esco"] >= 0.0
assert (recommendation["match_esco"] + result["improvement_esco"] <= 1.00001)

#Acquiring Hadoop must give it exact coverage.

hadoop_after = next(
    item
    for item in result["affected_skills"]
    if item["skill_id"] == NEW_SKILL_ID
)

assert hadoop_after["new_coverage"] == 1.0
assert hadoop_after["old_coverage"] == 0.0


#VERIFY IMPROVEMENT FORMULA
reconstructed_improvement = (
    sum(
        item["coverage_increase"]
        for item in result["affected_skills"]
    )
    / result["canonical_skill_count"]
)

assert abs(reconstructed_improvement - result["improvement_esco"]) < 1e-9

print("\nALL TESTS PASSED")


#Show affected skills
print("\n" + "=" * 80)
print("SKILLS IMPROVED BY ACQUIRING HADOOP")
print("=" * 80)

for item in result["affected_skills"]:
    print("Skill:", item["skill_name"])
    print("Old coverage:",
        f"{item['old_coverage']:.4f}"
    )
    print("New coverage:",
        f"{item['new_coverage']:.4f}"
    )
    print("Coverage increase:",
        f"{item['coverage_increase']:.4f}"
    )

    print("-" * 80)

#TEST 2— VERIFY AGAINST FULL RECALCULATION
print("\n" + "=" * 80)
print("FULL RECALCULATION TEST")
print("=" * 80)

updated_user_skills = USER_SKILL_IDS + [NEW_SKILL_ID]

updated_recommendation = recommend_occupation(occupation_id=TARGET_OCCUPATION_ID, user_skill_ids=updated_user_skills)

actual_improvement = (updated_recommendation["match_esco"] - recommendation["match_esco"])

predicted_improvement = result["improvement_esco"]

print(
    "Predicted improvement:",
    f"{predicted_improvement * 100:.4f} percentage points"
)

print(
    "Actual improvement:",
    f"{actual_improvement * 100:.4f} percentage points"
)

assert abs(actual_improvement - predicted_improvement) < 1e-4, "Predicted and actual improvements differ."

print("\nFULL RECALCULATION TEST PASSED")

#TEST 3— MULTIPLE SKILL IMPROVEMENT

print("\n" + "=" * 80)
print("MULTIPLE SKILL IMPROVEMENT TEST")
print("=" * 80)

#Search among missing canonical skills.
#Do not test skills already owned by the user.

candidate_skills = [
    item
    for item in skill_gaps
    if item["skill_id"] not in USER_SKILL_IDS
    and item["coverage"] < 1.0
]

selected_candidate = None
selected_result = None

for candidate in candidate_skills:
    candidate_result = calculate_match_improvement(
        skill_gaps=skill_gaps,
        new_skill_id=candidate["skill_id"]
    )

    #We want at least two improved skills, including at least one semantic improvement.

    has_semantic_improvement = any(
        affected["skill_id"] != candidate["skill_id"]
        for affected in candidate_result["affected_skills"]
    )

    if (candidate_result["affected_skill_count"] >= 2 and has_semantic_improvement):
        selected_candidate = candidate
        selected_result = candidate_result
        break


#VERIFY THAT A SUITABLE CANDIDATE WAS FOUND

assert selected_candidate is not None, ("No candidate with multiple skill improvements was found.")

print("Selected new skill:", selected_candidate["skill_name"])

print("Affected skills:", selected_result["affected_skill_count"])

print(
    "Predicted improvement:",
    f"{selected_result['improvement_esco'] * 100:.4f} "
    "percentage points"
)


#FULL RECALCULATION
updated_user_skills = (USER_SKILL_IDS + [selected_candidate["skill_id"]])

updated_recommendation = recommend_occupation(occupation_id=TARGET_OCCUPATION_ID, user_skill_ids=updated_user_skills)

actual_improvement = (updated_recommendation["match_esco"] - recommendation["match_esco"])

predicted_improvement = (selected_result["improvement_esco"])

print(
    "Actual improvement:",
    f"{actual_improvement * 100:.4f} "
    "percentage points"
)

assert abs(actual_improvement - predicted_improvement) < 1e-4, ("Predicted and actual improvements differ.")
assert selected_result["affected_skill_count"] >= 2

print("\nMULTIPLE SKILL IMPROVEMENT TEST PASSED")


#Show all affected skills
print("\n" + "=" * 80)
print("AFFECTED SKILLS")
print("=" * 80)

for item in selected_result["affected_skills"]:
    improvement_type = (
        "EXACT"
        if item["skill_id"] == selected_candidate["skill_id"]
        else "SEMANTIC"
    )

    print("Skill:", item["skill_name"])
    print("Improvement type:", improvement_type)
    print(
        "Old coverage:",
        f"{item['old_coverage']:.4f}"
    )
    print(
        "New coverage:",
        f"{item['new_coverage']:.4f}"
    )
    print(
        "Coverage increase:",
        f"{item['coverage_increase']:.4f}"
    )
    print("-" * 80)