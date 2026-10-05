import sys
import os
from pathlib import Path
from dotenv import load_dotenv
from neo4j import GraphDatabase

PROJECT_ROOT = Path(__file__).resolve().parents[2]

sys.path.insert(0, str(PROJECT_ROOT))

from src.graph_skill_similarity import (find_related_skills_for_skill)
from src.occupation_similarity import (find_similar_occupations)
from src.explainability.graph_explanation import (generate_skill_graph_explanation, generate_occupation_graph_explanation)

load_dotenv()

NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USER = os.getenv("NEO4J_USER")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")

if not NEO4J_URI or not NEO4J_USER or not NEO4J_PASSWORD:
    raise RuntimeError("Neo4j environment variables are required.")

DATA_SCIENTIST_ID = ("258e46f9-0075-4a2e-adae-1ff0477e0f30")

driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

with driver.session() as session:
    skill_query = """
    MATCH (o:Occupation)-[:ESCO_REQUIRES]->(s:Skill)
    WITH
        s,
        count(DISTINCT o) AS occupation_count
    WHERE occupation_count >= 2
    RETURN
        s.esco_id AS skill_id,
        s.name AS skill_name,
        occupation_count
    ORDER BY
        occupation_count DESC,
        skill_name
    LIMIT 1
    """
    skill_record = session.run(skill_query).single()

    assert skill_record is not None, ("Could not find a skill with at least two ESCO occupation neighbors.")

    TEST_SKILL_ID = skill_record["skill_id"]

    print("Selected test skill:", skill_record["skill_name"])
    print("Occupation count:", skill_record["occupation_count"])

    skill_graph_result = (find_related_skills_for_skill(session=session, skill_id=TEST_SKILL_ID, top_n=5,min_shared_occupations=1))

    skill_graph_explanation = (generate_skill_graph_explanation(skill_graph_result))

    assert (skill_graph_explanation["explanation_type"] == "skill_graph")
    assert (skill_graph_explanation["skill_id"] == skill_graph_result["skill_id"])
    assert (skill_graph_explanation["skill_name"] == skill_graph_result["skill_name"])
    assert (skill_graph_explanation["ranking_criterion"] == skill_graph_result["ranking_criterion"])
    assert (skill_graph_explanation["occupation_count"] == skill_graph_result["occupation_count"])
    assert (skill_graph_explanation["general_explanation"])
    assert (len(skill_graph_explanation["related_skills"]) == len(skill_graph_result["related_skills"]))

    for original, explained in zip(skill_graph_result["related_skills"], skill_graph_explanation["related_skills"]):
        assert (explained["rank"] == original["rank"])
        assert (explained["skill_id"] == original["skill_id"]) 
        assert (explained["skill_name"] == original["skill_name"])
        assert abs(explained["jaccard_similarity"] - original["jaccard_similarity"]) < 1e-12
        assert (explained["shared_occupation_count"] == original["shared_occupation_count"])
        assert (explained["union_occupation_count"] == original["union_occupation_count"])
        assert (explained["explanation_text"])

    occupation_graph_result = (find_similar_occupations(session=session, current_occupation_id=DATA_SCIENTIST_ID, top_n=5, min_shared_skills=1)    )

    occupation_graph_explanation = (generate_occupation_graph_explanation(occupation_graph_result))

    assert (occupation_graph_explanation["explanation_type"] == "occupation_graph")
    assert (occupation_graph_explanation["current_occupation_id"] == occupation_graph_result["current_occupation_id"])
    assert (occupation_graph_explanation["current_occupation_name"] == occupation_graph_result["current_occupation_name"])
    assert (occupation_graph_explanation["similarity_method"] == occupation_graph_result["similarity_method"])
    assert (occupation_graph_explanation["current_occupation_skill_count"] == occupation_graph_result["current_occupation_skill_count"])
    assert (occupation_graph_explanation["general_explanation"])
    assert (len(occupation_graph_explanation["similar_occupations"]) == len(occupation_graph_result["similar_occupations"]))

    for original, explained in zip(occupation_graph_result["similar_occupations"], occupation_graph_explanation["similar_occupations"]):
        assert (explained["rank"] == original["rank"])
        assert (explained["occupation_id"] == original["occupation_id"])
        assert (explained["occupation_name"] == original["occupation_name"])
        assert abs(explained["jaccard_similarity"] - original["jaccard_similarity"]) < 1e-12
        assert (explained["shared_skill_count"] == original["shared_skill_count"])
        assert (explained["union_skill_count"] == original["union_skill_count"])
        assert (explained["explanation_text"])

    print("=" * 80)
    print("SKILL GRAPH EXPLANATION")
    print("=" * 80)

    print(skill_graph_explanation["general_explanation"])
    print("\nRelated skills:\n")
    for item in skill_graph_explanation["related_skills"]:
        print(
            f"Rank {item['rank']}: "
            f"{item['skill_name']}"
        )
        print("  Jaccard:",
            f"{item['jaccard_percent']:.2f}%"
        )
        print("  Shared occupations:", item["shared_occupation_count"])
        print("  Union occupations:", item["union_occupation_count"])
        print("  Explanation:")
        print(" ", item["explanation_text"])
        print("-" * 80)

    print("\n" + "=" * 80)
    print("OCCUPATION GRAPH EXPLANATION")
    print("=" * 80)

    print(occupation_graph_explanation["general_explanation"])
    print("\nSimilar occupations:\n")
    for item in occupation_graph_explanation["similar_occupations"]:
        print(
            f"Rank {item['rank']}: "
            f"{item['occupation_name']}"
        )
        print("  ISCO:", item["isco_group"])
        print("  Jaccard:",
            f"{item['jaccard_percent']:.2f}%"
        )
        print("  Shared canonical skills:", item["shared_skill_count"])
        print("  Union canonical skills:", item["union_skill_count"])
        print("  Explanation:")
        print(" ", item["explanation_text"])
        print("-" * 80)


print("\n" + "=" * 80)
print("GRAPH EXPLANATION TEST PASSED")
print("=" * 80)

driver.close()