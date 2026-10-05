import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(
    0,
    str(PROJECT_ROOT)
)

from src.recommendation_engine import (recommend_occupation)
from src.explainability.job_match_explanation import (generate_job_match_explanation)

#TEST INPUT
TARGET_OCCUPATION_ID = (
    "258e46f9-0075-4a2e-adae-1ff0477e0f30"
)

TARGET_OCCUPATION_NAME = "Data Scientist"

USER_SKILL_IDS = [
    "5f0082ab-2131-49b5-94d6-a1821daf57d6",
    "505e4ef3-7ce4-437d-b7b4-5c608f71c258",
    "25f0ea33-b4a2-4f31-b7b4-7d20e827b180"
]

#1. GENERATE RECOMMENDATION RESULT
recommendation_result = recommend_occupation(
    occupation_id=TARGET_OCCUPATION_ID,
    user_skill_ids=USER_SKILL_IDS
)

#2. GENERATE EXPLANATION
explanation = generate_job_match_explanation(
    occupation_name=TARGET_OCCUPATION_NAME,
    recommendation_result=recommendation_result
)

#3. BASIC VALIDATION
assert (
    explanation["explanation_type"]
    == "job_match"
)

assert (
    explanation["occupation_name"]
    == TARGET_OCCUPATION_NAME
)

assert abs(
    explanation["match_esco"]
    - recommendation_result["match_esco"]
) < 1e-12

assert (
    explanation["canonical_skill_count"]
    == recommendation_result["canonical_skill_count"]
)

assert (
    explanation["exact_match_count"]
    == recommendation_result["exact_match_count"]
)

assert (
    explanation["semantic_match_count"]
    == recommendation_result["semantic_match_count"]
)

assert (
    explanation["missing_skill_count"]
    == recommendation_result["missing_skill_count"]
)

assert abs(
    explanation["average_gap"]
    - recommendation_result["average_gap"]
) < 1e-12

assert (
    explanation["match_market"]
    == recommendation_result["match_market"]
)

assert (
    explanation["both_skill_count"]
    == recommendation_result["both_skill_count"]
)

assert (
    explanation["market_reason"]
    == recommendation_result["market_reason"]
)

#4. VALIDATE DISPLAY VALUES
assert abs(
    explanation["match_esco_percent"]
    - (
        recommendation_result["match_esco"]
        * 100
    )
) < 1e-10

assert abs(
    explanation["average_gap_percent"]
    - (
        recommendation_result["average_gap"]
        * 100
    )
) < 1e-10

if recommendation_result["match_market"] is not None:

    assert explanation["market_available"] is True

    assert abs(
        explanation["match_market_percent"]
        - (
            recommendation_result["match_market"]
            * 100
        )
    ) < 1e-10

else:

    assert explanation["market_available"] is False

    assert (
        explanation["match_market_percent"]
        is None
    )


#5. VALIDATE TEXT OUTPUT
assert explanation["esco_explanation"]

assert explanation["market_explanation"]

assert explanation["explanation_text"]

assert TARGET_OCCUPATION_NAME in (
    explanation["esco_explanation"]
)

assert (
    f"{explanation['match_esco_percent']:.2f}%"
    in explanation["esco_explanation"]
)

if explanation["market_available"]:

    assert (
        f"{explanation['match_market_percent']:.2f}%"
        in explanation["market_explanation"]
    )


#6. PRINT RESULT
print("=" * 80)
print("JOB MATCH EXPLANATION TEST")
print("=" * 80)

print(
    "Occupation:",
    explanation["occupation_name"]
)

print(
    "MatchESCO:",
    f"{explanation['match_esco_percent']:.4f}%"
)

print(
    "MatchMarket:",
    (
        f"{explanation['match_market_percent']:.4f}%"
        if explanation["match_market_percent"] is not None
        else "N/A"
    )
)

print(
    "Canonical skills:",
    explanation["canonical_skill_count"]
)

print(
    "Exact matches:",
    explanation["exact_match_count"]
)

print(
    "Semantic matches:",
    explanation["semantic_match_count"]
)

print(
    "Missing skills:",
    explanation["missing_skill_count"]
)

print(
    "Average gap:",
    f"{explanation['average_gap_percent']:.4f}%"
)


print("\n" + "=" * 80)
print("ESCO EXPLANATION")
print("=" * 80)

print(
    explanation["esco_explanation"]
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
print("JOB MATCH EXPLANATION TEST PASSED")
print("=" * 80)