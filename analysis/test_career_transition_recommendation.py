import sys
import os
from pathlib import Path
from dotenv import load_dotenv
from neo4j import GraphDatabase

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.career_transition_recommendation import (generate_career_transition_recommendations)

load_dotenv()

NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USER = os.getenv("NEO4J_USER")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")

if not NEO4J_URI or not NEO4J_USER or not NEO4J_PASSWORD:
    raise RuntimeError("Neo4j environment variables are required.")

CURRENT_OCCUPATION_ID = ("258e46f9-0075-4a2e-adae-1ff0477e0f30")

USER_SKILL_IDS = [
    "5f0082ab-2131-49b5-94d6-a1821daf57d6",
    "505e4ef3-7ce4-437d-b7b4-5c608f71c258",
    "25f0ea33-b4a2-4f31-b7b4-7d20e827b180"
]

driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

with driver.session() as session:
    result = (generate_career_transition_recommendations(
            session=session,
            current_occupation_id=CURRENT_OCCUPATION_ID,
            user_skill_ids=USER_SKILL_IDS,
            structural_top_n=10,
            recommendation_top_n=5,
            min_shared_skills=1
        )
    )

    recommendations = result["recommendations"]

    print("=" * 80)
    print("CAREER TRANSITION RECOMMENDATION TEST")
    print("=" * 80)

    print("Mode:", result["mode"])
    print("Current occupation:", result["current_occupation_name"])
    print("Current occupation ISCO:", result["current_occupation_isco_group"])
    print("Candidate pool:", result["candidate_pool_definition"])
    print("Structural similarity method:", result["structural_similarity_method"])
    print("Structural filtering role:", result["structural_filtering_role"])
    print("Final ranking criterion:", result["final_ranking_criterion"])
    print("Structural candidates evaluated:", result["evaluated_candidate_count"])
    print("Recommendations returned:", len(recommendations))

    assert (result["mode"] == "career_transition")
    assert (result["structural_similarity_method"] == "unweighted_jaccard")
    assert (result["structural_filtering_role"] == "candidate_generation_only")
    assert (result["final_ranking_criterion"] == "match_esco")
    assert (result["evaluated_candidate_count"] <= 10)
    assert len(recommendations) > 0
    assert len(recommendations) <= 5

    previous_match_esco = None
    seen_occupation_ids = set()

    for expected_rank, item in enumerate(recommendations, start=1):
        assert (item["rank"] == expected_rank)
        assert (item["occupation_id"] != CURRENT_OCCUPATION_ID)
        assert (item["occupation_id"] not in seen_occupation_ids)

        seen_occupation_ids.add(item["occupation_id"])
        assert (0.0 <= item["occupation_similarity"] <= 1.0)
        assert (0.0 <= item["match_esco"] <= 1.0)
        assert (item["shared_skill_count"] >= 1)
        assert (item["union_skill_count"] >= item["shared_skill_count"])
        assert (item["canonical_skill_count"] > 0)
        assert (item["missing_skill_count"] >= 0)
        assert (0.0 <= item["average_gap"] <= 1.0)

        if previous_match_esco is not None:
            assert (item["match_esco"] <= previous_match_esco + 1e-12)

        previous_match_esco = (item["match_esco"])

    print("\n" + "=" * 80)
    print("FINAL USER-SPECIFIC CAREER TRANSITIONS")
    print("=" * 80)

    for item in recommendations:
        print(
            f"Rank {item['rank']}: "
            f"{item['occupation_name']}"
        )
        print("  ISCO:", item["isco_group"])
        print("  Structural rank:", item["structural_rank"])
        print("  Occupation Jaccard:", 
        f"{item['occupation_similarity']:.4f}"
        )
        print("  Shared canonical skills:", item["shared_skill_count"])
        print("  Union canonical skills:", item["union_skill_count"])
        print("  MatchESCO:",
            f"{item['match_esco'] * 100:.4f}%"
        )
        if item["match_market"] is not None:
            print("  MatchMarket:",
                f"{item['match_market'] * 100:.4f}%"
            )

        else:
            print("  MatchMarket: N/A")
            print("  Market reason:", item["market_reason"])

        print("  Canonical skills:", item["canonical_skill_count"])
        print("  Exact matches:", item["exact_match_count"])
        print("  Semantic matches:", item["semantic_match_count"])
        print("  Missing skills:", item["missing_skill_count"])
        print("  Average gap:",
            f"{item['average_gap']:.4f}"
        )

        print("-" * 80)


    print("\n" + "=" * 80)
    print("STRUCTURAL VS USER-SPECIFIC RANKING")
    print("=" * 80)

    structural_order = sorted(recommendations, key=lambda item: item["structural_rank"])

    print("Structural order among returned recommendations:")

    for item in structural_order:
        print(
            f"  Structural rank "
            f"{item['structural_rank']}: "
            f"{item['occupation_name']} "
            f"(J={item['occupation_similarity']:.4f})"
        )

    print("\nFinal user-specific order:")

    for item in recommendations:
        print(
            f"  Final rank "
            f"{item['rank']}: "
            f"{item['occupation_name']} "
            f"(MatchESCO="
            f"{item['match_esco'] * 100:.4f}%)"
        )


    structural_ids = [item["occupation_id"]
        for item in structural_order
    ]

    final_ids = [item["occupation_id"]
        for item in recommendations
    ]

    if structural_ids == final_ids:
        print("\nFor this user profile, the final MatchESCO order matches the structural order among the returned occupations.")

    else:
        print("\nThe final user-specific ranking differs from the structural Jaccard order.")
        print("This shows that structural similarity and user readiness are distinct signals.")


print("\n" + "=" * 80)
print("CAREER TRANSITION RECOMMENDATION TEST PASSED")
print("=" * 80)

driver.close()