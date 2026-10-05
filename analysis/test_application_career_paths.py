import sys
import os
from pathlib import Path
from dotenv import load_dotenv
from neo4j import GraphDatabase

PROJECT_ROOT = Path(__file__).resolve().parent.parent

sys.path.insert(0, str(PROJECT_ROOT))

from src.application_service import (analyze_career_paths)

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

try:
    with driver.session() as session:
        transition = (
            analyze_career_paths(
                session=session,
                user_skill_ids=USER_SKILL_IDS,
                current_occupation_id=CURRENT_OCCUPATION_ID,
                structural_top_n=10,
                recommendation_top_n=5,
                min_shared_skills=1
            )
        )

        assert (transition["analysis_type"] == "career_paths")
        assert (transition["mode"] == "career_transition")
        assert (transition["current_occupation_id"] == CURRENT_OCCUPATION_ID)
        assert (transition["user_skill_count"] == len(USER_SKILL_IDS))

        transition_result = (transition["career_result"])
        assert (transition_result["mode"] == "career_transition")
        assert (transition_result["current_occupation_id"] == CURRENT_OCCUPATION_ID)
        assert (transition_result["final_ranking_criterion"] == "match_esco")
        assert (len(transition_result["recommendations"]) > 0)
        assert (len(transition_result["recommendations"]) <= 5)

        transition_explanation = (transition["explanation"])

        assert (transition_explanation["explanation_type"] == "career_transition")
        assert (transition_explanation["current_occupation_id"] == CURRENT_OCCUPATION_ID)
        assert (transition_explanation["ranking_criterion"] == "match_esco")
        assert (transition_explanation["general_explanation"])

        transition_recommendations = (transition_result["recommendations"])

        for index in range(len(transition_recommendations) - 1):
            current_match = (transition_recommendations[index]["match_esco"])

            next_match = (transition_recommendations[index + 1]["match_esco"])

            assert (current_match >= next_match)


        discovery = (analyze_career_paths(
                session=session,
                user_skill_ids=USER_SKILL_IDS,
                current_occupation_id=None,
                recommendation_top_n=5
            )
        )

        assert (discovery["analysis_type"] == "career_paths")
        assert (discovery["mode"] == "career_discovery")
        assert (discovery["current_occupation_id"] is None)
        assert (discovery["user_skill_count"] == len(USER_SKILL_IDS))

        discovery_result = (discovery["career_result"])

        assert (discovery_result["mode"] == "career_discovery")
        assert (discovery_result["final_ranking_criterion"] == "match_esco")
        assert (discovery_result["candidate_count"] > 0)
        assert (len(discovery_result["recommendations"]) > 0)
        assert (len(discovery_result["recommendations"]) <= 5)

        discovery_explanation = (discovery["explanation"])

        assert (discovery_explanation["explanation_type"] == "career_discovery")
        assert (discovery_explanation["ranking_criterion"] == "match_esco")
        assert (discovery_explanation["candidate_count"] == discovery_result["candidate_count"])
        assert (discovery_explanation["general_explanation"])

        discovery_recommendations = (discovery_result["recommendations"])

        for index in range(len(discovery_recommendations) - 1):
            current_match = (discovery_recommendations[index]["match_esco"])

            next_match = (discovery_recommendations[index + 1]["match_esco"])

            assert (current_match >= next_match)

        print("=" * 80)
        print("APPLICATION CAREER PATHS TEST")
        print("=" * 80)

        print("\nCAREER TRANSITION")
        print("-" * 80)
        print("Mode:", transition["mode"])
        print("Current occupation:", transition_result["current_occupation_name"])
        print("Structural candidates:", transition_result.get("structural_candidate_count", "N/A"))
        print("\nFinal transition recommendations:\n")

        for item in transition_recommendations:
            print(
                f"Rank {item['rank']}: "
                f"{item['occupation_name']}"
            )
            print("  Structural rank:", item["structural_rank"])
            print(
                "  Jaccard:",
                f"{item['occupation_similarity'] * 100:.4f}%"
            )
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
            print("-" * 80)

        print("\nTRANSITION EXPLANATION")
        print("-" * 80)

        print(transition_explanation["general_explanation"])

        print("\n" + "=" * 80)
        print("CAREER DISCOVERY")
        print("=" * 80)

        print("Mode:", discovery["mode"])

        print("Candidate count:", discovery_result["candidate_count"])

        print("\nFinal discovery recommendations:\n")

        for item in discovery_recommendations:
            print(
                f"Rank {item['rank']}: "
                f"{item['occupation_name']}"
            )
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
            print("-" * 80)

        print("\nDISCOVERY EXPLANATION")
        print("-" * 80)

        print(discovery_explanation["general_explanation"])

        print("\n" + "=" * 80)
        print("APPLICATION CAREER PATHS TEST PASSED")
        print("=" * 80)
finally:
    driver.close()