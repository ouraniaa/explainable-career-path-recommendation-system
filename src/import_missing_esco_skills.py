"""
Imports canonical ESCO skills that are missing from the Neo4j knowledge graph.

This file was created after we found that the original graph import did not contain
all of the canonical ESCO skills used by the analytical occupation profiles. That
created an inconsistency between the profile data and the graph: some official ESCO
requirements existed in the CSV profiles but had no corresponding Skill node in Neo4j.

The script compares the canonical ESCO skill set (ESCO_ONLY and BOTH) with the Skill
nodes already stored in Neo4j and imports only the missing ones. This keeps the graph
complete and aligned with the ESCO vocabulary used by the recommendation system.
"""
import pandas as pd
import os

from dotenv import load_dotenv
from neo4j import GraphDatabase

load_dotenv()

PROFILE_FILE = "data/processed/occupation_skill_profiles.csv"

URI = os.getenv("NEO4J_URI")
USER = os.getenv("NEO4J_USER")
PASSWORD = os.getenv("NEO4J_PASSWORD")

if not URI or not USER or not PASSWORD:
    raise RuntimeError("Neo4j environment variables are required.")

def load_missing_esco_skills():
    """Load the unique canonical ESCO skills required by the analytical profiles."""
    df = pd.read_csv(PROFILE_FILE)

    esco_skills = df[df["source_type"].isin(["ESCO_ONLY", "BOTH"])][["skill_id", "skill_name"]]

    esco_skills = (
        esco_skills
        .dropna(subset=["skill_id"])
        .drop_duplicates(subset=["skill_id"])
    )

    return esco_skills


def get_existing_skill_ids(session):
    """Return the ESCO skill IDs that already exist as Skill nodes in Neo4j."""
    result = session.run("""
        MATCH (s:Skill)
        WHERE s.esco_id IS NOT NULL
        RETURN s.esco_id AS skill_id
    """)

    return {
        record["skill_id"]
        for record in result
        if record["skill_id"] is not None
    }


def import_missing_skills():
    esco_skills = load_missing_esco_skills()

    driver = GraphDatabase.driver(URI, auth=(USER, PASSWORD))

    with driver.session() as session:
        existing_ids = get_existing_skill_ids(session)

        missing_skills = esco_skills[~esco_skills["skill_id"].isin(existing_ids)].copy()

        if missing_skills.empty:
            driver.close()
            return

        records = missing_skills.to_dict("records")

        session.run("""
            UNWIND $rows AS row

            MERGE (s:Skill {esco_id: row.skill_id})

            SET s.name = row.skill_name,
                s.source = CASE
                    WHEN s.source IS NULL THEN 'ESCO'
                    ELSE s.source
                END
        """, rows=records)


    driver.close()


if __name__ == "__main__":
    import_missing_skills()