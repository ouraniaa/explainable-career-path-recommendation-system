import sys
import os
from pathlib import Path
from dotenv import load_dotenv
from neo4j import GraphDatabase

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.occupation_similarity import (get_occupation_skill_neighbors, calculate_occupation_jaccard_similarity, get_ict_candidate_occupations, find_similar_occupations)

load_dotenv()

NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USER = os.getenv("NEO4J_USER")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")

if not NEO4J_URI or not NEO4J_USER or not NEO4J_PASSWORD:
    raise RuntimeError("Neo4j environment variables are required.")

DATA_SCIENTIST_ID = ("258e46f9-0075-4a2e-adae-1ff0477e0f30")

driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

with driver.session() as session:
    print("=" * 80)
    print("1. OCCUPATION SKILL NEIGHBORHOOD")
    print("=" * 80)

    current = get_occupation_skill_neighbors(session=session, occupation_id=DATA_SCIENTIST_ID)

    print("Occupation:", current["occupation_name"])
    print("Occupation ID:", current["occupation_id"])
    print("ISCO group:", current["isco_group"])
    print("Canonical ESCO skill count:", current["skill_count"])

    assert (current["occupation_id"] == DATA_SCIENTIST_ID)
    assert (current["skill_count"] > 0)

    print("\n" + "=" * 80)
    print("2. ICT CANDIDATE POOL")
    print("=" * 80)

    candidates = get_ict_candidate_occupations(session=session)

    print("Candidate occupation count:", len(candidates))

    assert len(candidates) > 0

    for candidate in candidates:
        isco_group = (candidate["isco_group"] or "")

        assert (isco_group.startswith("25") or isco_group.startswith("35") or isco_group == "1330")

    print("\nFirst 10 candidate occupations:")

    for candidate in candidates[:10]:
        print("-", candidate["occupation_name"], "| ISCO:", candidate["isco_group"], "| Skills:", candidate["skill_count"])

    print("\n" + "=" * 80)
    print("3. TOP STRUCTURALLY SIMILAR OCCUPATIONS")
    print("=" * 80)

    result = find_similar_occupations(
        session=session,
        current_occupation_id=DATA_SCIENTIST_ID,
        top_n=10,
        min_shared_skills=1
    )

    print("Current occupation:", result["current_occupation_name"])
    print("Current occupation ISCO:", result["current_occupation_isco_group"])
    print("Current skill count:", result["current_occupation_skill_count"])
    print("Candidate pool definition:", result["candidate_pool_definition"])
    print("Candidate count before filtering:", result["candidate_count_before_filtering"])
    print("Candidate count after filtering:", result["candidate_count_after_filtering"])
    print("Returned top-N:", result["returned_count"])

    similar = result["similar_occupations"]

    assert (result["similarity_method"] == "unweighted_jaccard")
    assert (result["returned_count"] <= 10)
    assert len(similar) > 0

    previous_similarity = None

    for expected_rank, item in enumerate(similar, start=1):
        assert (item["rank"] == expected_rank)
        assert (item["occupation_id"] != DATA_SCIENTIST_ID)
        assert (0.0 <= item["jaccard_similarity"] <= 1.0)
        assert (item["shared_skill_count"] >= 1)
        assert (item["union_skill_count"] >= item["shared_skill_count"])

        if previous_similarity is not None:
            assert (item["jaccard_similarity"] <= previous_similarity + 1e-12)

        previous_similarity = (item["jaccard_similarity"])

    print("\nTop similar occupations:\n")

    for item in similar:
        print(
            f"Rank {item['rank']}: "
            f"{item['occupation_name']}"
        )
        print("  ISCO:", item["isco_group"])
        print("  Jaccard:", f"{item['jaccard_similarity']:.4f}")
        print("  Shared skills:", item["shared_skill_count"]
        )
        print("  Union skills:", item["union_skill_count"])
        print("  Candidate skill count:", item["candidate_skill_count"])
        print("-" * 80)

    top_candidate = similar[0]

    pair_result = (calculate_occupation_jaccard_similarity(session=session, occupation_a_id=DATA_SCIENTIST_ID, occupation_b_id=top_candidate["occupation_id"]))

    assert abs(pair_result["jaccard_similarity"] - top_candidate["jaccard_similarity"]) < 1e-12
    assert (pair_result["shared_skill_count"] == top_candidate["shared_skill_count"])
    assert (pair_result["union_skill_count"] == top_candidate["union_skill_count"])

    print("\n" + "=" * 80)
    print("PAIRWISE VALIDATION")
    print("=" * 80)

    print(pair_result["occupation_a_name"], "<->", pair_result["occupation_b_name"])

    print("Jaccard:", f"{pair_result['jaccard_similarity']:.4f}")

    print("Shared skills:", pair_result["shared_skill_count"])
    print("Union skills:", pair_result["union_skill_count"])


print("\n" + "=" * 80)
print("OCCUPATION SIMILARITY TEST PASSED")
print("=" * 80)

driver.close()