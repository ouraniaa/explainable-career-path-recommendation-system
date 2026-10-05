import sys
import os
from pathlib import Path
from dotenv import load_dotenv
from neo4j import GraphDatabase

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.personalized_skill_recommendation import (generate_personalized_skill_recommendations)
load_dotenv()

TARGET_OCCUPATION_ID = ("258e46f9-0075-4a2e-adae-1ff0477e0f30")

USER_SKILL_IDS = [
    "5f0082ab-2131-49b5-94d6-a1821daf57d6",
    "505e4ef3-7ce4-437d-b7b4-5c608f71c258",
    "25f0ea33-b4a2-4f31-b7b4-7d20e827b180"
]


URI = os.getenv("NEO4J_URI")
USER = os.getenv("NEO4J_USER")
PASSWORD = os.getenv("NEO4J_PASSWORD")

if not URI or not USER or not PASSWORD:
    raise RuntimeError("Neo4j environment variables are required.")

driver = GraphDatabase.driver(URI, auth=(USER, PASSWORD))

try:
    with driver.session() as session:
        result = generate_personalized_skill_recommendations(
            session=session,
            occupation_id=TARGET_OCCUPATION_ID,
            user_skill_ids=USER_SKILL_IDS,
            top_n=5,
            graph_top_n=3
        )

        recommendations = result["recommendations"]

        print("=" * 80)
        print("PERSONALIZED SKILL RECOMMENDATION TEST")
        print("=" * 80)

        print("Canonical skills:", result["canonical_skill_count"])
        print("Candidate skills:", result["total_candidate_skills"])
        print("Recommendations returned:", result["recommendation_count"])
        print("Ranking criterion:", result["ranking_criterion"])
        print("Graph similarity method:", result["graph_similarity_method"])
        print("Graph signal role:", result["graph_signal_role"])

        assert result["canonical_skill_count"] == 97
        assert result["total_candidate_skills"] == 94
        assert result["recommendation_count"] == 5
        assert len(recommendations) == 5
        assert (result["ranking_criterion"] == "improvement_esco")
        assert (result["graph_similarity_method"] == "unweighted_jaccard")
        assert (result["graph_signal_role"] == "explanatory_only")

        assert [item["rank"]
            for item in recommendations 
        ] == [1, 2, 3, 4, 5]

        improvements = [item["improvement_esco"]
            for item in recommendations
        ]

        assert improvements == sorted(improvements, reverse=True)

        for item in recommendations:
            assert item["skill_id"]
            assert item["skill_name"]
            assert item["recommendation_type"] == ("canonical_esco_skill")
            assert (0.0 <= item["current_coverage"] <= 1.0)
            assert (0.0 <= item["residual_gap"] <= 1.0)
            assert item["improvement_esco"] >= 0.0
            assert item["direct_improvement"] >= 0.0
            assert item["semantic_spillover"] >= 0.0
            assert (0.0 <= item["semantic_dependency_ratio"] <= 1.0)

            assert isinstance(item["structurally_related_skills"], list)
            assert len(item["structurally_related_skills"] ) <= 3

            for related in item["structurally_related_skills"]:
                assert related["skill_id"]
                assert related["skill_name"]
                assert (0.0 < related["jaccard_similarity"] <= 1.0)
                assert (related["shared_occupation_count"] >= 1)
                assert (related["union_occupation_count"] >= related["shared_occupation_count"])

            assert isinstance(item["explanation"], str)
            assert len(item["explanation"] ) > 0


        print("\nPERSONALIZED SKILLRECOMMENDATION TEST PASSED")

        print("\n" + "=" * 80)
        print("TOP 5 PERSONALIZED RECOMMENDATIONS")
        print("=" * 80)

        for item in recommendations:
            print(f"Rank: {item['rank']}")
            print(f"Skill: {item['skill_name']}")
            print(
                f"ESCO relation: "
                f"{item['relation_type']}"
            )
            print("Residual gap:",
                f"{item['residual_gap']:.4f}"
            )
            print("ESCO Improvement:",
                f"{item['improvement_esco'] * 100:.4f} percentage points"
            )
            print("Direct Improvement:",
                f"{item['direct_improvement'] * 100:.4f} percentage points"
            )
            print("Semantic Spillover:",
                f"{item['semantic_spillover'] * 100:.4f} percentage points"
            )
            print("Semantic Dependency Ratio:",
                f"{item['semantic_dependency_ratio']:.4f}"
            )

            if item["rca"] is not None:
                print("RCA:", f"{item['rca']:.4f}")
            else:
                print("RCA: N/A")

            if item["improvement_market"] is not None:
                print("Market Improvement:",
                    f"{item['improvement_market'] * 100:.4f} percentage points"
                )
            else:
                print("Market Improvement: N/A")

            print("\nStructurally related skills:")

            related_skills = item["structurally_related_skills"]

            if related_skills:
                for related in related_skills:
                    print(
                        f"  {related['rank']}. "
                        f"{related['skill_name']}"
                    )
                    print("     Jaccard:", f"{related['jaccard_similarity']:.4f}")
                    print("     Shared occupations:", related["shared_occupation_count"])
                    print("     Union occupations:", related["union_occupation_count"])

            else:
                print("  No structurally related skills found.")
            print("\nExplanation:")
            print(item["explanation"])

            print("-" * 80)

finally:

    driver.close()