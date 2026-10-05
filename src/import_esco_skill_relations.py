"""
Imports official ESCO occupation-skill relations into Neo4j.

This script reads the processed ESCO relation data and creates ESCO_REQUIRES
relationships between Occupation and Skill nodes in the knowledge graph.

The importer is kept separate from the analytical code so the graph can be rebuilt
or refreshed without changing the recommendation logic itself.
"""

import pandas as pd
import os

from dotenv import load_dotenv
from neo4j import GraphDatabase

load_dotenv()

CSV_FILE = "data/raw/occupationSkillRelations_en.csv"

NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USER = os.getenv("NEO4J_USER")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")

if not NEO4J_URI or not NEO4J_USER or not NEO4J_PASSWORD:
    raise RuntimeError("Neo4j environment variables are required.")

BATCH_SIZE = 1000

def extract_uuid(uri: str) -> str:
    """
    Converts:
    http://data.europa.eu/esco/occupation/<uuid>
    http://data.europa.eu/esco/skill/<uuid>

    into:
    <uuid>
    """
    if pd.isna(uri):
        return ""

    return str(uri).rstrip("/").split("/")[-1]


#Loads official ESCO occupation-skill relations
df = pd.read_csv(CSV_FILE)

df["occupation_id"] = df["occupationUri"].apply(extract_uuid)
df["skill_id"] = df["skillUri"].apply(extract_uuid)

df = df[
    [
        "occupation_id",
        "skill_id",
        "relationType",
        "skillType"
    ]
].copy()

df = df.rename(
    columns={
        "relationType": "relation_type",
        "skillType": "skill_type"
    }
)

df = df[
    (df["occupation_id"] != "")
    & (df["skill_id"] != "")
]


print("=" * 90)
print("ESCO RELATION IMPORT")
print("=" * 90)
print(f"Official rows loaded: {len(df)}")

driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

query = """
UNWIND $rows AS row

MATCH (o:Occupation {
    esco_id: row.occupation_id
})

MATCH (s:Skill {
    esco_id: row.skill_id
})

MERGE (o)-[r:ESCO_REQUIRES]->(s)

SET
    r.relation_type = row.relation_type,
    r.skill_type = row.skill_type
"""

total_processed = 0

with driver.session() as session:
    records = df.to_dict("records")

    for start in range(
        0,
        len(records),
        BATCH_SIZE
    ):

        batch = records[start:start + BATCH_SIZE]

        session.run(query, rows=batch)

        total_processed += len(batch)

        print(
            f"Processed "
            f"{total_processed}/{len(records)} "
            f"official relations..."
        )

driver.close()


print("\n")
print("=" * 90)
print("IMPORT COMPLETED")
print("=" * 90)

print("Official ESCO relations processed:", total_processed)

print(
    "\nNote: only relations where BOTH the Occupation and Skill already existed in Neo4j were created."
)