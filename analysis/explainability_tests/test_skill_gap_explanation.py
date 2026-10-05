import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]

sys.path.insert(
    0,
    str(PROJECT_ROOT)
)

from src.learning_priority import (calculate_learning_priority)
from src.explainability.skill_gap_explanation import (generate_skill_gap_explanation)

#TEST INPUT
TARGET_OCCUPATION_ID = (
    "258e46f9-0075-4a2e-adae-1ff0477e0f30"
)

USER_SKILL_IDS = [
    "5f0082ab-2131-49b5-94d6-a1821daf57d6",
    "505e4ef3-7ce4-437d-b7b4-5c608f71c258",
    "25f0ea33-b4a2-4f31-b7b4-7d20e827b180"
]

#1. GENERATE LEARNING PRIORITY RESULT
priority_result = calculate_learning_priority(
    occupation_id=TARGET_OCCUPATION_ID,
    user_skill_ids=USER_SKILL_IDS,
    top_n=5
)

ranked_skills = priority_result[
    "ranked_skills"
]

assert len(ranked_skills) > 0

top_skill = ranked_skills[0]

#2. GENERATE SKILL GAP EXPLANATION
explanation = generate_skill_gap_explanation(
    ranked_skill=top_skill
)

#3. BASIC VALIDATION
assert (
    explanation["explanation_type"]
    == "skill_gap"
)

assert (
    explanation["skill_id"]
    == top_skill["skill_id"]
)

assert (
    explanation["skill_name"]
    == top_skill["skill_name"]
)

assert (
    explanation["relation_type"]
    == top_skill["relation_type"]
)

assert (
    explanation["match_type"]
    == top_skill["match_type"]
)

#4. VALIDATE CORE GAP VALUES
assert abs(
    explanation["current_coverage"]
    - top_skill["current_coverage"]
) < 1e-12

assert abs(
    explanation["residual_gap"] - top_skill["residual_gap"]
) < 1e-12

assert abs(
    explanation["improvement_esco"] - top_skill["improvement_esco"]
) < 1e-12

assert abs(
    explanation["direct_improvement"] - top_skill["direct_improvement"]
) < 1e-12

assert abs(
    explanation["semantic_spillover"] - top_skill["semantic_spillover"]
) < 1e-12

assert abs(
    explanation["semantic_dependency_ratio"] - top_skill["semantic_dependency_ratio"]
) < 1e-12


#5. VALIDATE DISPLAY PERCENTAGES
assert abs(
    explanation["current_coverage_percent"] - (top_skill["current_coverage"] * 100)
) < 1e-10

assert abs(
    explanation["residual_gap_percent"] - (top_skill["residual_gap"] * 100)
) < 1e-10

assert abs(
    explanation["improvement_esco_percent"] - (top_skill["improvement_esco"] * 100)
) < 1e-10

assert abs(
    explanation["direct_improvement_percent"] - (top_skill["direct_improvement"] * 100)
) < 1e-10

assert abs(
    explanation["semantic_spillover_percent"] - (top_skill["semantic_spillover"] * 100)
) < 1e-10

assert abs(
    explanation["semantic_dependency_percent"] - (top_skill["semantic_dependency_ratio"] * 100)
) < 1e-10


#6. VALIDATE MARKET VALUES
assert (
    explanation["rca"] == top_skill["rca"]
)

assert (
    explanation["market_gap_severity"] == top_skill["market_gap_severity"]
)

assert (
    explanation["improvement_market"] == top_skill["improvement_market"]
)

if top_skill["improvement_market"] is not None:

    assert (
        explanation["improvement_market_percent"] is not None
    )

    assert abs(
        explanation["improvement_market_percent"] - (top_skill["improvement_market"] * 100)
    ) < 1e-10

else:

    assert (
        explanation["improvement_market_percent"] is None
    )


#7. VALIDATE AFFECTED SKILLS
assert (
    explanation["affected_esco_skill_count"] == top_skill["affected_esco_skill_count"]
)

assert (
    explanation["affected_esco_skills"] == top_skill["affected_esco_skills"]
)

assert (
    explanation["affected_market_skills"] == top_skill["affected_market_skills"]
)


#8. VALIDATE TEXT OUTPUT
assert explanation["gap_explanation"]

assert explanation["improvement_explanation"]

assert explanation["semantic_explanation"]

assert explanation["market_explanation"]

assert explanation["explanation_text"]

assert (
    top_skill["skill_name"] in explanation["explanation_text"]
)

assert (
    f"{explanation['improvement_esco_percent']:.2f}" in explanation["improvement_explanation"]
)

#9. PRINT RESULT
print("=" * 80)
print("SKILL GAP EXPLANATION TEST")
print("=" * 80)

print(
    "Skill:", 
    explanation["skill_name"]
)

print(
    "ESCO relation:", explanation["relation_type"]
)

print(
    "Match type:", explanation["match_type"]
)

print(
    "Current coverage:", f"{explanation['current_coverage_percent']:.4f}%"
)

print(
    "Residual gap:", f"{explanation['residual_gap_percent']:.4f}%"
)

print(
    "ImprovementESCO:", f"{explanation['improvement_esco_percent']:.4f}", "percentage points"
)

print(
    "Direct improvement:", f"{explanation['direct_improvement_percent']:.4f}", "percentage points"
)

print(
    "Semantic spillover:", f"{explanation['semantic_spillover_percent']:.4f}", "percentage points"
)

print(
    "Semantic dependency:", f"{explanation['semantic_dependency_percent']:.4f}%"
)

print(
    "Affected ESCO skills:", explanation["affected_esco_skill_count"]
)


if explanation["rca"] is not None:

    print(
        "RCA:", f"{explanation['rca']:.4f}"
    )

else:

    print(
        "RCA: N/A"
    )


if explanation["market_gap_severity"] is not None:

    print(
        "Market Gap Severity:", f"{explanation['market_gap_severity']:.4f}"
    )

else:

    print(
        "Market Gap Severity: N/A"
    )


if explanation["improvement_market_percent"] is not None:

    print(
        "ImprovementMarket:", f"{explanation['improvement_market_percent']:.4f}", "percentage points"
    )

else:

    print(
        "ImprovementMarket: N/A"
    )


print("\n" + "=" * 80)
print("GAP EXPLANATION")
print("=" * 80)

print(
    explanation["gap_explanation"]
)


print("\n" + "=" * 80)
print("IMPROVEMENT EXPLANATION")
print("=" * 80)

print(
    explanation["improvement_explanation"]
)


print("\n" + "=" * 80)
print("SEMANTIC EXPLANATION")
print("=" * 80)

print(
    explanation["semantic_explanation"]
)


print("\n" + "=" * 80)
print("MARKET EXPLANATION")
print("=" * 80)

print(
    explanation["market_explanation"]
)


print("\n" + "=" * 80)
print("FULL EXPLANATION")
print("=" * 80)

print(
    explanation["explanation_text"]
)


print("\n" + "=" * 80)
print("SKILL GAP EXPLANATION TEST PASSED")
print("=" * 80)