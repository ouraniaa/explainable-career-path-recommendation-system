import sys
import os
from pathlib import Path
from dotenv import load_dotenv
from neo4j import GraphDatabase

PROJECT_ROOT = Path(__file__).resolve().parent.parent

sys.path.insert(0, str(PROJECT_ROOT))

from src.application_service import (analyze_target_occupation)

load_dotenv()

NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USER = os.getenv("NEO4J_USER")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")

if not NEO4J_URI or not NEO4J_USER or not NEO4J_PASSWORD:
    raise RuntimeError("Neo4j environment variables are required.")

TARGET_OCCUPATION_ID = ("258e46f9-0075-4a2e-adae-1ff0477e0f30")

TARGET_OCCUPATION_NAME = ("data scientist")

USER_SKILL_IDS = [
    "5f0082ab-2131-49b5-94d6-a1821daf57d6",
    "505e4ef3-7ce4-437d-b7b4-5c608f71c258",
    "25f0ea33-b4a2-4f31-b7b4-7d20e827b180"
]

driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))


try:
    with driver.session() as session:
        result = (analyze_target_occupation(
                session=session,
                occupation_id=TARGET_OCCUPATION_ID,
                occupation_name=TARGET_OCCUPATION_NAME,
                user_skill_ids=USER_SKILL_IDS,
                learning_priority_top_n=5,
                graph_top_n=3,
                roadmap_max_steps=5
            )
        )

        assert (result["analysis_type"] == "target_occupation")
        assert (result["occupation"]["occupation_id"] == TARGET_OCCUPATION_ID)
        assert (result["occupation"]["occupation_name"] == TARGET_OCCUPATION_NAME)
        assert (result["user_skill_count"] == len(USER_SKILL_IDS))

        recommendation = (result["recommendation"])
        assert (recommendation["occupation_id"] == TARGET_OCCUPATION_ID)
        assert (0.0 <= recommendation["match_esco"] <= 1.0)
        assert (recommendation["canonical_skill_count"] > 0)
        assert (recommendation["skill_gaps"])
        assert (recommendation["esco_details"])

        learning_priority = (result["learning_priority"])
        ranked_skills = (learning_priority["ranked_skills"])
        
        assert (len(ranked_skills) > 0)
        assert (len(ranked_skills) <= 5)

        top_skill = (ranked_skills[0])
        assert (top_skill["improvement_esco"] >= 0.0)

        personalized_skills = (result["personalized_skill_recommendations"])

        assert (personalized_skills["occupation_id"] == TARGET_OCCUPATION_ID)
        assert (personalized_skills["graph_signal_role"] == "explanatory_only")
        assert (personalized_skills["graph_similarity_method"] == "unweighted_jaccard")

        roadmap = (result["roadmap"])
        assert (roadmap["occupation_id"] == TARGET_OCCUPATION_ID)
        assert (roadmap["selection_strategy"] == "greedy")
        assert (roadmap["selection_method"] == "sequential_marginal_improvement_esco")
        assert (roadmap["roadmap_step_count"] <= 5)
        assert (roadmap["roadmap_step_count"] == len(roadmap["roadmap_steps"]))
        assert (roadmap["final_match_esco"] >= roadmap["initial_match_esco"])
       
        explanations = (result["explanations"])
        assert (explanations["job_match"] is not None)
        assert (explanations["top_skill_gap"] is not None)
        assert (explanations["roadmap"] is not None)
        assert (explanations["overall"] is not None)

        assert (explanations["job_match"]["explanation_type"] == "job_match")

        assert (explanations["top_skill_gap"]["explanation_type"] == "skill_gap")
        assert (explanations["top_skill_gap"]["skill_id"] == top_skill["skill_id"])

        assert (explanations["roadmap"]["explanation_type"] == "career_skill_roadmap")

        assert (explanations["overall"]["explanation_type"] == "overall")
        assert (explanations["overall"]["explanation_text"])

        assert abs(explanations["job_match"]["match_esco"] - recommendation["match_esco"]) < 1e-12
        assert abs(explanations["roadmap"]["initial_match_esco"] - roadmap["initial_match_esco"]) < 1e-12
        assert abs(explanations["roadmap"]["final_match_esco"] - roadmap["final_match_esco"]) < 1e-12

        print("=" * 80)
        print("APPLICATION SERVICE TEST")
        print("=" * 80)

        print("Analysis type:", result["analysis_type"])
        print("Occupation:", result["occupation"]["occupation_name"])
        print("User skill count:", result["user_skill_count"])
        print("MatchESCO:",
            f"{recommendation['match_esco'] * 100:.4f}%"
        )
        if recommendation["match_market"] is not None:
            print("MatchMarket:",
                f"{recommendation['match_market'] * 100:.4f}%"
            )
        else:
            print("MatchMarket: N/A")
        print("Canonical skills:", recommendation["canonical_skill_count"])
        print("Missing skills:", recommendation["missing_skill_count"])

        print("\n" + "=" * 80)
        print("TOP LEARNING PRIORITIES")
        print("=" * 80)

        for skill in ranked_skills:
            print(
                f"Rank {skill['rank']}: "
                f"{skill['skill_name']}"
            )
            print("  ImprovementESCO:",
                f"{skill['improvement_esco'] * 100:.4f}, percentage points"
            )

        print("\n" + "=" * 80)
        print("ROADMAP")
        print("=" * 80)

        print("Initial MatchESCO:",
            f"{roadmap['initial_match_esco'] * 100:.4f}%"
        )

        for step in roadmap["roadmap_steps"]:
            print(
                f"Step {step['step']}: "
                f"{step['skill_name']}"
            )
            print(
                " ",
                f"{step['match_esco_before'] * 100:.4f}%"
                " -> "
                f"{step['match_esco_after'] * 100:.4f}%"
            )
        print("Final MatchESCO:",
            f"{roadmap['final_match_esco'] * 100:.4f}%"
        )

        print("\n" + "=" * 80)
        print("OVERALL EXPLANATION")
        print("=" * 80)

        print(explanations["overall"]["explanation_text"])

        print("\n" + "=" * 80)
        print("APPLICATION SERVICE TEST PASSED")
        print("=" * 80)

finally:
    driver.close()