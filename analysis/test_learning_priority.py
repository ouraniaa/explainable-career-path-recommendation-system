import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

sys.path.insert(0, str(PROJECT_ROOT))

from src.learning_priority import calculate_learning_priority

TARGET_OCCUPATION_ID = (
    "258e46f9-0075-4a2e-adae-1ff0477e0f30"
)

USER_SKILL_IDS = [
    "5f0082ab-2131-49b5-94d6-a1821daf57d6",
    "505e4ef3-7ce4-437d-b7b4-5c608f71c258",
    "25f0ea33-b4a2-4f31-b7b4-7d20e827b180"
]


#1. CALCULATE LEARNING PRIORITY
result = calculate_learning_priority(
    occupation_id=TARGET_OCCUPATION_ID,
    user_skill_ids=USER_SKILL_IDS,
    top_n=10
)

ranked_skills = result["ranked_skills"]


print("=" * 80)
print("LEARNING PRIORITY RANKING TEST")
print("=" * 80)

print("Canonical skills:", result["canonical_skill_count"])
print("Total candidate skills:", result["total_candidate_skills"])
print("Ranking criterion:", result["ranking_criterion"])
print("Returned skills:", len(ranked_skills))


assert result["canonical_skill_count"] == 97
assert result["total_candidate_skills"] == 94
assert result["ranking_criterion"] == "improvement_esco"
assert len(ranked_skills) == 10

#Improvement must be sorted descending.
improvements = [
    item["improvement_esco"]
    for item in ranked_skills
]

assert improvements == sorted(
    improvements,
    reverse=True
)


#Candidates must have residual gaps.
assert all(
    item["residual_gap"] > 0.0
    for item in ranked_skills
)


#Already owned skills must be excluded.
assert all(
    item["skill_id"] not in USER_SKILL_IDS
    for item in ranked_skills
)


#Score must remain within valid limits.
assert all(
    0.0 <= item["improvement_esco"] <= 1.0
    for item in ranked_skills
)


#No duplicate candidate skills.
assert len({
    item["skill_id"]
    for item in ranked_skills
}) == len(ranked_skills)


print("\nLEARNING PRIORITY TEST PASSED")

#VERIFY IMPROVEMENT DECOMPOSITION
for item in ranked_skills:
    reconstructed_improvement = (item["direct_improvement"] + item["semantic_spillover"])

    assert abs(
        reconstructed_improvement
        - item["improvement_esco"]
    ) < 1e-9

    assert item["direct_improvement"] >= 0.0
    assert item["semantic_spillover"] >= 0.0
    assert (0.0 <= item["semantic_dependency_ratio"] <= 1.0)

print("\nIMPROVEMENT DECOMPOSITION TEST PASSED")

#VERIFY BUSINESS ANALYTICS EXAMPLE
business_analytics = next(
    item
    for item in ranked_skills
    if item["skill_name"].lower() == "business analytics"
)

assert business_analytics["semantic_spillover"] > 0.0

assert business_analytics["semantic_dependency_ratio"] > 0.0

print("BUSINESS ANALYTICS SEMANTIC "
    "SPILLOVER TEST PASSED"
)


print("\n" + "=" * 80)
print("TOP 10 LEARNING PRIORITIES")
print("=" * 80)

for item in ranked_skills:
    print(f"Rank: {item['rank']}")
    print(f"Skill: {item['skill_name']}")
    print(f"ESCO relation: {item['relation_type']}")
    print(f"Residual gap: {item['residual_gap']:.4f}")
    print(
        "ESCO Improvement:",
        f"{item['improvement_esco'] * 100:.4f} "
        "percentage points"
    )
    print(
        "Direct Improvement:",
        f"{item['direct_improvement'] * 100:.4f} "
        "percentage points"
    )
    print(
        "Semantic Spillover:",
        f"{item['semantic_spillover'] * 100:.4f} "
        "percentage points"
    )
    print(
        "Semantic Dependency Ratio:",
        f"{item['semantic_dependency_ratio']:.4f}"
    )
    if item["rca"] is not None:
        print(f"RCA: {item['rca']:.4f}")
        print(
            "Market Gap Severity:",
            f"{item['market_gap_severity']:.4f}"
        )
    else:
        print("RCA: N/A")
        print("Market Gap Severity: N/A")

    if item["improvement_market"] is not None:
        print(
            "Market Improvement:",
            f"{item['improvement_market'] * 100:.4f} "
            "percentage points"
        )
    else:
        print("Market Improvement: N/A")
    print("Affected ESCO skills:", item["affected_esco_skill_count"])

    print("-" * 80)