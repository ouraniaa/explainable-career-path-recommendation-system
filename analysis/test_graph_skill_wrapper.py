import sys
import os
from pathlib import Path
from dotenv import load_dotenv
from neo4j import GraphDatabase

PROJECT_ROOT = Path(__file__).resolve().parent.parent

sys.path.insert(0, str(PROJECT_ROOT))

from src.graph_skill_similarity import (find_related_skills_for_skill)

load_dotenv()

URI = os.getenv("NEO4J_URI")
USER = os.getenv("NEO4J_USER")
PASSWORD = os.getenv("NEO4J_PASSWORD")

if not URI or not USER or not PASSWORD:
    raise RuntimeError("Neo4j environment variables are required.")


driver = GraphDatabase.driver(URI, auth=(USER, PASSWORD))

try:
    with driver.session() as session:

        query = """
        MATCH (s:Skill)
        WHERE toLower(s.name) = 'data mining'

        RETURN
            s.esco_id AS skill_id,
            s.name AS skill_name

        LIMIT 1
        """
        target = session.run(query).single()

        assert target is not None, ("Target skill 'data mining' was not found.")

        target_skill_id = target["skill_id"]

        result = find_related_skills_for_skill(session=session, skill_id=target_skill_id, top_n=5, min_shared_occupations=1)
        related = result["related_skills"]

        assert result["skill_id"] == target_skill_id
        assert result["skill_name"] == "data mining"
        assert (result["ranking_criterion"] == "jaccard_similarity")

        assert len(related) <= 5
        assert len(related) > 0

        assert all(item["skill_id"] != target_skill_id
            for item in related
        )
        assert all(0.0 < item["jaccard_similarity"] <= 1.0
            for item in related
        )
        assert all(item["shared_occupation_count"] >= 1
            for item in related
        )

        similarities = [
            item["jaccard_similarity"]
            for item in related
        ]

        assert similarities == sorted(similarities, reverse=True)

        print("=" * 80)
        print("GRAPH SKILL WRAPPER INTEGRATION TEST")
        print("=" * 80)

        print("Target skill:", result["skill_name"])
        print("Target occupation count:", result["occupation_count"])
        print("Candidate skills:", result["candidate_count"])
        print("Returned related skills:", result["related_skill_count"])
        print("Ranking criterion:", result["ranking_criterion"])
        print("\nGRAPH SKILL WRAPPER TEST PASSED")

        print("\n" + "=" * 80)
        print("TOP RELATED SKILLS")
        print("=" * 80)

        for item in related:
            print(f"Rank: {item['rank']}")
            print(f"Skill: {item['skill_name']}")
            print("Jaccard:", f"{item['jaccard_similarity']:.4f}")
            print("Shared occupations:", item["shared_occupation_count"])
            print("Union occupations:", item["union_occupation_count"])

            print("-" * 80)

finally:
    driver.close()