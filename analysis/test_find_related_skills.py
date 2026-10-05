import sys
import os
from pathlib import Path
from dotenv import load_dotenv
from neo4j import GraphDatabase

PROJECT_ROOT = Path(__file__).resolve().parent.parent

sys.path.insert(0, str(PROJECT_ROOT))

from src.graph_skill_similarity import (find_related_skills)

load_dotenv()

URI = os.getenv("NEO4J_URI")
USER = os.getenv("NEO4J_USER")
PASSWORD = os.getenv("NEO4J_PASSWORD")

if not URI or not USER or not PASSWORD:
    raise RuntimeError("Neo4j environment variables are required.")

driver = GraphDatabase.driver(URI, auth=(USER, PASSWORD))

try:
    with driver.session() as session:
        target_query = """
        MATCH (s:Skill)
        WHERE toLower(s.name) = 'computer programming'

        RETURN
            s.esco_id AS skill_id,
            s.name AS skill_name

        LIMIT 1
        """
        target = session.run(target_query).single()
        assert target is not None, ("computer programming skill not found.")
        target_skill_id = target["skill_id"]

        candidate_query = """
        MATCH
            (target:Skill {esco_id: $skill_id})

        MATCH
            (o:Occupation)-[:ESCO_REQUIRES]->(target)

        MATCH
            (o)-[:ESCO_REQUIRES]->(candidate:Skill)

        WHERE
            candidate.esco_id <> target.esco_id

        RETURN DISTINCT
            candidate.esco_id AS skill_id
        """
        candidate_records = session.run(candidate_query, skill_id=target_skill_id)

        candidate_skill_ids = [
            record["skill_id"]
            for record in candidate_records
        ]

        assert len(candidate_skill_ids) > 0

        result = find_related_skills(
            session=session,
            skill_id=target_skill_id,
            candidate_skill_ids=candidate_skill_ids,
            top_n=10,
            min_shared_occupations=1
        )

        related = result["related_skills"]

        print("=" * 80)
        print("TOP STRUCTURALLY RELATED SKILLS")
        print("=" * 80)

        print("Target skill:", result["skill_name"])
        print("Target occupation count:", result["occupation_count"])
        print("Candidate skills:", result["candidate_count"])
        print("Returned related skills:", result["related_skill_count"])
        print("Ranking criterion:", result["ranking_criterion"])

        assert (result["ranking_criterion"] == "jaccard_similarity")
        assert len(related) <= 10
        assert all(item["skill_id"] != target_skill_id
            for item in related
        )

        assert all(0.0 < item["jaccard_similarity"] <= 1.0 for item in related)
        assert all(item["shared_occupation_count"] >= 1 for item in related)

        similarities = [
            item["jaccard_similarity"]
            for item in related
        ]

        assert similarities == sorted(similarities, reverse=True)

        assert len({
            item["skill_id"]
            for item in related
        }) == len(related)

        print("\nRELATED SKILLS TEST PASSED")

        print("\n" + "=" * 80)
        print("RESULTS")
        print("=" * 80)

        for item in related:
            print(f"Rank: {item['rank']}")
            print(f"Skill: {item['skill_name']}")
            print("Jaccard:",
                f"{item['jaccard_similarity']:.4f}"
            )
            print("Shared occupations:", item["shared_occupation_count"])
            print("Candidate occupations:", item["candidate_occupation_count"])
            print("Union occupations:", item["union_occupation_count"])

            print("-" * 80)

        print("\n" + "=" * 80)
        print("ADDITIONAL TARGET SKILL TESTS")
        print("=" * 80)

        TARGET_SKILL_NAMES = ["data mining", "cyber security"]

        for target_name in TARGET_SKILL_NAMES:
            target_query = """
            MATCH (s:Skill)
            WHERE toLower(s.name) = toLower($skill_name)

            RETURN
                s.esco_id AS skill_id,
                s.name AS skill_name

            LIMIT 1
            """
            target = session.run(target_query, skill_name=target_name).single()

            if target is None:
                print(f"\nSKIPPED: '{target_name}' was not found in Neo4j.")
                continue

            target_skill_id = target["skill_id"]
            candidate_query = """
            MATCH
                (target:Skill {esco_id: $skill_id})

            MATCH
                (o:Occupation)-[:ESCO_REQUIRES]->(target)

            MATCH
                (o)-[:ESCO_REQUIRES]->(candidate:Skill)

            WHERE
                candidate.esco_id <> target.esco_id

            RETURN DISTINCT
                candidate.esco_id AS skill_id
            """

            candidate_records = session.run(candidate_query, skill_id=target_skill_id)

            candidate_skill_ids = [record["skill_id"]
                for record in candidate_records
            ]

            result = find_related_skills(
                session=session,
                skill_id=target_skill_id,
                candidate_skill_ids=candidate_skill_ids,
                top_n=10,
                min_shared_occupations=1
            )

            related = result["related_skills"]

            assert result["ranking_criterion"] == "jaccard_similarity"
            assert all(0.0 < item["jaccard_similarity"] <= 1.0
                for item in related
            )

            assert all(item["shared_occupation_count"] >= 1 
                for item in related
            )

            similarities = [item["jaccard_similarity"] 
                for item in related
            ]

            assert similarities == sorted(similarities, reverse=True)

            print("\n" + "-" * 80)

            print("Target skill:", result["skill_name"])
            print("Target occupation count:", result["occupation_count"])
            print("Candidate skills:", result["candidate_count"])
            print("Returned related skills:", result["related_skill_count"])

            print("-" * 80)

            for item in related:
                print(
                    f"Rank {item['rank']}: "
                    f"{item['skill_name']}"
                )
                print("  Jaccard:",
                    f"{item['jaccard_similarity']:.4f}"
                )
                print("  Shared occupations:", item["shared_occupation_count"])
                print("  Candidate occupations:", item["candidate_occupation_count"])
                print("  Union occupations:", item["union_occupation_count"])

            print(
                f"\nSANITY CHECK PASSED "
                f"FOR: {result['skill_name']}"
            )
finally:
    driver.close()