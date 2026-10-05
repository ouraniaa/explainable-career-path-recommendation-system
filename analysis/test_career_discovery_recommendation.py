import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(
    0,
    str(PROJECT_ROOT)
)

from src.career_transition_recommendation import (generate_career_discovery_recommendations, get_discovery_candidate_occupations)

USER_SKILL_IDS = [
    "5f0082ab-2131-49b5-94d6-a1821daf57d6",
    "505e4ef3-7ce4-437d-b7b4-5c608f71c258",
    "25f0ea33-b4a2-4f31-b7b4-7d20e827b180"
]

#1. TEST DISCOVERY CANDIDATE POOL
print("=" * 80)
print("1. CAREER DISCOVERY CANDIDATE POOL")
print("=" * 80)

candidates = get_discovery_candidate_occupations()

print("Candidate occupation count:", len(candidates))

assert len(candidates) > 0

occupation_ids = [
    candidate["occupation_id"]
    for candidate in candidates
]

assert len(occupation_ids) == len(set(occupation_ids))

for candidate in candidates:
    assert candidate["occupation_id"]
    assert candidate["occupation_name"]
    assert candidate["isco_group"]


print("\nFirst 10 candidate occupations:")

for candidate in candidates[:10]:

    print(
        "-",
        candidate["occupation_name"],
        "| ISCO:",
        candidate["isco_group"]
    )


#2. GENERATE CAREER DISCOVERY RECOMMENDATIONS
result = (
    generate_career_discovery_recommendations(
        user_skill_ids=USER_SKILL_IDS,
        recommendation_top_n=5
    )
)

recommendations = result["recommendations"]

#3. GENERAL SUMMARY
print("\n" + "=" * 80)
print("2. CAREER DISCOVERY RECOMMENDATION TEST")
print("=" * 80)

print("Mode:", result["mode"])

print("Candidate pool:", result["candidate_pool"])

print("Candidate count:", result["candidate_count"])

print("Final ranking criterion:", result["final_ranking_criterion"])

print("Recommendations returned:", len(recommendations))

#4. BASIC VALIDATION
assert (result["mode"] == "career_discovery")
assert (result["candidate_pool"] == "analytical_occupation_profile")
assert (result["candidate_count"] == len(candidates))
assert (result["final_ranking_criterion"] == "match_esco")

assert len(recommendations) > 0
assert len(recommendations) <= 5

#5. VALIDATE FINAL RANKING
previous_match_esco = None
seen_occupation_ids = set()

for expected_rank, item in enumerate(
    recommendations,
    start=1
):

    assert (item["rank"] == expected_rank)
    assert (item["occupation_id"] not in seen_occupation_ids)
    seen_occupation_ids.add(item["occupation_id"])
    assert (0.0 <= item["match_esco"] <= 1.0)
    assert (item["canonical_skill_count"] > 0)
    assert (item["exact_match_count"] >= 0)
    assert (item["semantic_match_count"] >= 0)
    assert (item["missing_skill_count"] >= 0)
    assert (0.0 <= item["average_gap"] <= 1.0)

    #Final ranking must be descending by MatchESCO.
    if previous_match_esco is not None:
        assert (item["match_esco"] <= previous_match_esco + 1e-12)

    previous_match_esco = (item["match_esco"])

print("\n" + "=" * 80)
print("3. TOP CAREER DISCOVERY RECOMMENDATIONS")
print("=" * 80)

for item in recommendations:
    print(
        f"Rank {item['rank']}: "
        f"{item['occupation_name']}"
    )
    print("  ISCO:", item["isco_group"])
    print(
        "  MatchESCO:",
        f"{item['match_esco'] * 100:.4f}%"
    )

    if item["match_market"] is not None:
        print(
            "  MatchMarket:",
            f"{item['match_market'] * 100:.4f}%"
        )
    else:
        print("  MatchMarket: N/A")
        print("  Market reason:", item["market_reason"])

    print("  Canonical skills:", item["canonical_skill_count"])
    print("  Exact matches:", item["exact_match_count"])
    print("  Semantic matches:", item["semantic_match_count"])
    print("  Missing skills:", item["missing_skill_count"])
    print("  Average gap:", f"{item['average_gap']:.4f}")
    print("-" * 80)


#TOP RESULT SHOULD HAVE MAXIMUM MATCHESCO
top_match_esco = max(
    item["match_esco"]
    for item in recommendations
)

assert abs(
    recommendations[0]["match_esco"]
    - top_match_esco
) < 1e-12


print("\n" + "=" * 80)
print("CAREER DISCOVERY RECOMMENDATION TEST PASSED")
print("=" * 80)