import sys
import os
from pathlib import Path
from dotenv import load_dotenv
from neo4j import GraphDatabase

PROJECT_ROOT = Path(__file__).resolve().parent.parent

sys.path.insert(0, str(PROJECT_ROOT))

from src.graph_skill_similarity import (get_skill_occupation_neighbors, calculate_jaccard_similarity)

load_dotenv()

URI = os.getenv("NEO4J_URI")
USER = os.getenv("NEO4J_USER")
PASSWORD = os.getenv("NEO4J_PASSWORD")

if not URI or not USER or not PASSWORD:
    raise RuntimeError("Neo4j environment variables are required.")

driver = GraphDatabase.driver(URI, auth=(USER, PASSWORD))

try:
    with driver.session() as session:
        pair_query = """
        MATCH
            (o:Occupation)-[:ESCO_REQUIRES]->(s1:Skill)

        MATCH
            (o)-[:ESCO_REQUIRES]->(s2:Skill)

        WHERE
            s1.esco_id < s2.esco_id

        RETURN
            s1.esco_id AS skill_a_id,
            s1.name AS skill_a_name,
            s2.esco_id AS skill_b_id,
            s2.name AS skill_b_name,
            o.esco_id AS shared_occupation_id,
            o.name AS shared_occupation_name

        LIMIT 1
        """
        pair = session.run(pair_query).single()

        assert pair is not None, ("Could not find two skills sharing an ESCO occupation.")

        skill_a_id = pair["skill_a_id"]
        skill_b_id = pair["skill_b_id"]

        neighbors_a = (get_skill_occupation_neighbors(session=session, skill_id=skill_a_id))
        neighbors_b = (get_skill_occupation_neighbors(session=session,skill_id=skill_b_id))

        print("=" * 80)
        print("GRAPH SKILL SIMILARITY TEST")
        print("=" * 80)

        print("Skill A:", neighbors_a["skill_name"])
        print("Skill B:", neighbors_b["skill_name"])
        print("Known shared occupation:", pair["shared_occupation_name"])
        print("Skill A occupation count:", neighbors_a["occupation_count"])
        print("Skill B occupation count:", neighbors_b["occupation_count"])

        assert (pair["shared_occupation_id"] in neighbors_a["occupation_ids"])
        assert (pair["shared_occupation_id"] in neighbors_b["occupation_ids"])
        print("\nNEIGHBOR RETRIEVAL TEST PASSED")

        result = calculate_jaccard_similarity(session=session, skill_a_id=skill_a_id, skill_b_id=skill_b_id)

        print("\n" + "=" * 80)
        print("JACCARD RESULT")
        print("=" * 80)
        print("Shared occupations:", result["shared_occupation_count"])
        print("Union occupations:", result["union_occupation_count"])
        print("Jaccard similarity:", f"{result['jaccard_similarity']:.4f}")

        manual_intersection = (neighbors_a["occupation_ids"] & neighbors_b["occupation_ids"])
        manual_union = (neighbors_a["occupation_ids"] | neighbors_b["occupation_ids"])
        manual_jaccard = (len(manual_intersection) / len(manual_union))

        assert (result["shared_occupation_count"] == len(manual_intersection))
        assert (result["union_occupation_count"] == len(manual_union))
        assert abs(result["jaccard_similarity"] - manual_jaccard) < 1e-12

        assert (0.0 <= result["jaccard_similarity"] <= 1.0)
        print("\nJACCARD CALCULATION TEST PASSED")

finally:
    driver.close()