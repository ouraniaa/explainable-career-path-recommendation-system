import sys
import os
from pathlib import Path

from dotenv import load_dotenv
from neo4j import GraphDatabase

PROJECT_ROOT = Path(__file__).resolve().parents[2]

sys.path.insert(0, str(PROJECT_ROOT))

from src.recommendation_engine import (recommend_occupation)
from src.learning_priority import (calculate_learning_priority)
from src.occupation_similarity import (find_similar_occupations)
from src.explainability.job_match_explanation import (generate_job_match_explanation)
from src.explainability.skill_gap_explanation import (generate_skill_gap_explanation)
from src.explainability.graph_explanation import (generate_occupation_graph_explanation)
from src.explainability.overall_explanation import (generate_overall_explanation)
from src.career_transition_recommendation import (generate_career_transition_recommendations)
from src.explainability.career_path_explanation import (generate_career_transition_explanation)

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

with driver.session() as session:
    recommendation_result = (
        recommend_occupation(occupation_id=TARGET_OCCUPATION_ID, user_skill_ids=USER_SKILL_IDS)
    )

    job_match_explanation = (generate_job_match_explanation(occupation_name=TARGET_OCCUPATION_NAME, recommendation_result=recommendation_result))

    priority_result = (
        calculate_learning_priority(
            occupation_id=TARGET_OCCUPATION_ID,
            user_skill_ids=USER_SKILL_IDS,
            top_n=5
        )
    )

    assert (len(priority_result["ranked_skills"]) > 0)
    top_skill = (priority_result["ranked_skills"][0])

    skill_gap_explanation = (generate_skill_gap_explanation(ranked_skill=top_skill))

    occupation_graph_result = (
        find_similar_occupations(session=session, current_occupation_id=TARGET_OCCUPATION_ID, top_n=5, min_shared_skills=1))

    graph_explanation = (generate_occupation_graph_explanation(occupation_graph_result))

    transition_result = (
        generate_career_transition_recommendations(
            session=session,
            current_occupation_id=TARGET_OCCUPATION_ID,
            user_skill_ids=USER_SKILL_IDS,
            structural_top_n=10,
            recommendation_top_n=5,
            min_shared_skills=1
        )
    )

    career_path_explanation = (generate_career_transition_explanation(transition_result))

    overall = (
        generate_overall_explanation(
            job_match_explanation=job_match_explanation,
            skill_gap_explanation=skill_gap_explanation,
            career_path_explanation=career_path_explanation,
            graph_explanation=graph_explanation
        )
    )

    assert (overall["explanation_type"] == "overall")
    assert ("job_match" in overall["included_sections"])
    assert ("skill_gap" in overall["included_sections"])
    assert ("graph" in overall["included_sections"])
    assert ("career_path" in overall["included_sections"])

    assert (overall["job_match_summary"] is not None)
    assert (overall["skill_gap_summary"] is not None)
    assert (overall["career_path_summary"] is not None)
    assert (overall["graph_summary"] is not None)
    assert (overall["methodology_summary"])
    assert (overall["explanation_text"])

    match_esco_text = (f"{job_match_explanation['match_esco_percent']:.2f}%")

    assert (match_esco_text in overall["job_match_summary"])
    assert (TARGET_OCCUPATION_NAME in overall["job_match_summary"])

    improvement_text = (f"{skill_gap_explanation['improvement_esco_percent']:.2f}")

    assert (top_skill["skill_name"] in overall["skill_gap_summary"])
    assert (improvement_text in overall["skill_gap_summary"])

    similar_occupations = (graph_explanation["similar_occupations"])

    assert (len(similar_occupations) > 0)
    top_related = (similar_occupations[0])

    assert (top_related["occupation_name"] in overall["graph_summary"])
    graph_jaccard_text = (f"{top_related['jaccard_percent']:.2f}%")

    assert (graph_jaccard_text in overall["graph_summary"])
    assert ("Career Transition" in overall["career_path_summary"])

    top_transition = (career_path_explanation["recommendations"][0])
    assert (top_transition["occupation_name"] in overall["career_path_summary"])

    assert (
        f"{top_transition['match_esco_percent']:.2f}%"
        in overall["career_path_summary"]
    )

    assert ("single combined score" in overall["methodology_summary"])
    assert ("MatchESCO" in overall["methodology_summary"])
    assert ("MatchMarket" in overall["methodology_summary"])
    assert ("graph" in overall["methodology_summary"].lower())
    assert ("ImprovementESCO" in overall["methodology_summary"])

    print("=" * 80)
    print("OVERALL EXPLANATION TEST")
    print("=" * 80)

    print("\nJOB MATCH SUMMARY")
    print("-" * 80)

    print(overall["job_match_summary"])

    print("\nSKILL GAP SUMMARY")
    print("-" * 80)
    print(overall["skill_gap_summary"])

    print("\nGRAPH SUMMARY")
    print("-" * 80)
    print(overall["graph_summary"])

    print("\nMETHODOLOGY SUMMARY")
    print("-" * 80)
    print(overall["methodology_summary"])

    print("\nCAREER PATH SUMMARY")
    print("-" * 80)
    print(overall["career_path_summary"])

    print("\nFULL OVERALL EXPLANATION")
    print("-" * 80)
    print(overall["explanation_text"])

print("\n" + "=" * 80)
print("OVERALL EXPLANATION TEST PASSED")
print("=" * 80)

driver.close()