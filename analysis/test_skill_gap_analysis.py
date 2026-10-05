import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.recommendation_engine import recommend_occupation
from src.skill_gap_analysis import calculate_skill_gaps


TARGET_OCCUPATION_ID = ("258e46f9-0075-4a2e-adae-1ff0477e0f30")

USER_SKILL_IDS = [
    "5f0082ab-2131-49b5-94d6-a1821daf57d6",
    "505e4ef3-7ce4-437d-b7b4-5c608f71c258",
    "25f0ea33-b4a2-4f31-b7b4-7d20e827b180"
]

recommendation = recommend_occupation(occupation_id=TARGET_OCCUPATION_ID, user_skill_ids=USER_SKILL_IDS)

result = calculate_skill_gaps(recommendation["esco_details"])


print("=" * 80)
print("SKILL GAP ANALYSIS TEST")
print("=" * 80)

print("Canonical skills:", result["canonical_skill_count"])
print("Exact matches:", result["exact_count"]) 
print("Semantic matches:", result["semantic_count"])
print("Missing skills:", result["missing_count"])
print("Average gap:", f"{result['average_gap']:.4f}")

assert result["canonical_skill_count"] == 97
assert (result["exact_count"] + result["semantic_count"] + result["missing_count"] == result["canonical_skill_count"])
assert result["exact_count"] == recommendation["exact_match_count"]
assert result["semantic_count"] == recommendation["semantic_match_count"]

assert all(
    0.0 <= item["gap"] <= 1.0
    for item in result["skill_gaps"]
)

assert all(
    abs(item["gap"] + item["coverage"] - 1.0) < 1e-9
    for item in result["skill_gaps"]
)

print("\nALL TESTS PASSED")


print("\n" + "=" * 80)
print("TOP 10 SKILL GAPS")
print("=" * 80)

for item in result["skill_gaps"][:10]:
    print(f"Skill: {item['skill_name']}")
    print(f"ESCO relation: {item['relation_type']}")
    print(f"Match type: {item['match_type']}")
    print(f"Coverage: {item['coverage']:.4f}")
    print(f"Gap: {item['gap']:.4f}")

    print("-" * 80)
    print("\n" + "=" * 80)
print("SEMANTIC SKILL GAPS")
print("=" * 80)

for item in result["skill_gaps"]:
    if item["match_type"] == "semantic":

        print(f"Required: {item['skill_name']}")
        print(
            f"Matched with: "
            f"{item['best_user_skill_name']}"
        )
        print(f"Coverage: {item['coverage']:.4f}")
        print(f"Gap: {item['gap']:.4f}")
        print("-" * 80)
