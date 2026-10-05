import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.recommendation_engine import recommend_occupation


TARGET_OCCUPATION_ID = ("258e46f9-0075-4a2e-adae-1ff0477e0f30")

USER_SKILL_IDS = [
    "5f0082ab-2131-49b5-94d6-a1821daf57d6",
    "505e4ef3-7ce4-437d-b7b4-5c608f71c258",
    "25f0ea33-b4a2-4f31-b7b4-7d20e827b180"
]


result = recommend_occupation(occupation_id=TARGET_OCCUPATION_ID, user_skill_ids=USER_SKILL_IDS)


print("=" * 80)
print("RECOMMENDATION ENGINE TEST")
print("=" * 80)

print("Occupation ID:", result["occupation_id"])
print("Canonical skills:", result["canonical_skill_count"])
print("BOTH skills:", result["both_skill_count"])
print("Exact matches:", result["exact_match_count"])
print("Semantic matches:", result["semantic_match_count"])

if result["match_esco"] is not None:
    print(
        "MatchESCO:",
        f"{result['match_esco'] * 100:.2f}%"
    )

if result["match_market"] is not None:
    print(
        "MatchMarket:",
        f"{result['match_market'] * 100:.2f}%"
    )
else:
    print("MatchMarket: N/A")

assert result["canonical_skill_count"] == 97
assert result["both_skill_count"] == 21
assert 0 <= result["match_esco"] <= 1
assert 0 <= result["match_market"] <= 1
print("\nRECOMMENDATION ENGINE TEST PASSED")

print("\n" + "=" * 80)
print("SKILL GAP INTEGRATION")
print("=" * 80)

print("Missing skills:", result["missing_skill_count"])
print(
    "Average gap:",
    f"{result['average_gap']:.4f}"
)

assert result["missing_skill_count"] == 91
assert abs(result["average_gap"] - (1 - result["match_esco"])) < 0.0001

print("\nSKILL GAP INTEGRATION PASSED")