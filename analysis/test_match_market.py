import sys
from pathlib import Path

import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.match_market import calculate_match_market

TARGET_OCCUPATION_ID = ("258e46f9-0075-4a2e-adae-1ff0477e0f30")

USER_SKILL_IDS = [
    "5f0082ab-2131-49b5-94d6-a1821daf57d6",
    "505e4ef3-7ce4-437d-b7b4-5c608f71c258",
    "25f0ea33-b4a2-4f31-b7b4-7d20e827b180",
]


# CALCULATE MATCH MARKET
result = calculate_match_market(occupation_id=TARGET_OCCUPATION_ID, user_skill_ids=USER_SKILL_IDS)

print("=" * 80)
print("MATCH MARKET TEST — DATA SCIENTIST")
print("=" * 80)

print("BOTH skills:", result["both_skill_count"])
print("Reason:", result.get("reason", "None"))

if result["match_market"] is None:
    print("MatchMarket: N/A")

else:
    print(
        "MatchMarket:",
        f"{result['match_market'] * 100:.2f}%"
    )

    print(
        "Total RCA:",
        round(result["total_rca"], 4)
    )

    print(
        "Weighted coverage sum:",
        round(result["weighted_coverage_sum"], 4)
    )

    # VERIFY MATHEMATICAL CALCULATION
    details = result["details"]

    calculated_numerator = sum(
        item["rca"] * item["coverage"]
        for item in details
    )

    calculated_denominator = sum(
        item["rca"]
        for item in details
    )

    reconstructed_score = (calculated_numerator / calculated_denominator)

    assert len(details) == 21, (f"Expected 21 BOTH skills, got {len(details)}")

    assert 0.0 <= result["match_market"] <= 1.0, ("MatchMarket must be between 0 and 1.")

    assert np.isclose(
        result["match_market"],
        reconstructed_score
    ), "Market score calculation is incorrect."

    assert all(
        details[i]["rca"] >= details[i + 1]["rca"]
        for i in range(len(details) - 1)
    ), "Details are not sorted by descending RCA."

    print("\nALL TESTS PASSED")

    # EXPLAINABILITY DETAILS
    print("\n" + "=" * 80)
    print("TOP 10 BOTH SKILLS BY RCA")
    print("=" * 80)

    for item in details[:10]:
        print(
            f"Skill: {item['skill_name']}"
        )
        print(
            f"RCA: {item['rca']:.4f}"
        )
        print(
            f"Coverage: {item['coverage']:.4f}"
        )
        print(
            f"Weighted coverage: "
            f"{item['weighted_coverage']:.4f}"
        )
        print("-" * 80)

