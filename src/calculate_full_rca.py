"""
Builds the full occupation-skill RCA diagnostic table used to inspect market evidence.

The script reads the official ESCO occupation-skill relations, retrieves deduplicated
job-posting skill observations from Neo4j, and calculates Revealed Comparative Advantage
(RCA) for each occupation-skill pair in the analytical scope. It also checks whether each
market-observed pair is officially supported by ESCO and exports the results for
diagnostic analysis.
"""
import pandas as pd
import os

from dotenv import load_dotenv
from neo4j import GraphDatabase

load_dotenv()

ESCO_RELATIONS_FILE = "occupationSkillRelations_en.csv"

NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USER = os.getenv("NEO4J_USER")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")

if not NEO4J_URI or not NEO4J_USER or not NEO4J_PASSWORD:
    raise RuntimeError("Neo4j environment variables are required.")

OUTPUT_FILE = "full_rca_diagnostic.csv"

def extract_uuid(uri: str) -> str:
    """Extract the UUID stored at the end of an ESCO URI."""
    if pd.isna(uri):
        return ""
    return str(uri).rstrip("/").split("/")[-1]

#This loads the official ESCO relations so market-observed pairs can be validated later.
esco_df = pd.read_csv(ESCO_RELATIONS_FILE)

esco_df["occupation_id"] = esco_df["occupationUri"].apply(extract_uuid)
esco_df["skill_id"] = esco_df["skillUri"].apply(extract_uuid)

official_relation_type = {
    (row["occupation_id"], row["skill_id"]): row["relationType"]
    for _, row in esco_df.iterrows()
}

official_pairs = set(official_relation_type.keys())

driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

query = """
MATCH (j:JobPosting)-[:BELONGS_TO]->(o:Occupation)
WHERE j.is_deduplicated = true
  AND (
      o.isco_group STARTS WITH '25'
      OR o.isco_group = '1330'
  )

WITH o, count(DISTINCT j) AS OccupationSupport

WHERE OccupationSupport >= 5

MATCH (j:JobPosting)-[:BELONGS_TO]->(o)
MATCH (j)-[:REQUIRES]->(s:Skill)

WHERE j.is_deduplicated = true

WITH
    o,
    s,
    OccupationSupport,
    count(DISTINCT j) AS x_os

RETURN
    o.esco_id AS occupation_id,
    o.name AS occupation,
    o.isco_group AS isco_group,
    OccupationSupport,
    s.esco_id AS skill_id,
    s.name AS skill,
    x_os
"""
with driver.session() as session:
    records = list(session.run(query))

driver.close()

rows = []

for record in records:
    rows.append({
        "occupation_id": record["occupation_id"],
        "occupation": record["occupation"],
        "isco_group": record["isco_group"],
        "occupation_support": record["OccupationSupport"],
        "skill_id": record["skill_id"],
        "skill": record["skill"],
        "x_os": record["x_os"]
    })

df = pd.DataFrame(rows)

#Total skill observations for each occupation: sum_s x(o,s).
occupation_totals = (df.groupby("occupation_id")["x_os"].sum().to_dict())

df["occupation_skill_total"] = df["occupation_id"].map(occupation_totals)

#Total observations of each skill across all occupations: sum_o x(o,s).
skill_totals = (df.groupby("skill_id")["x_os"].sum().to_dict())

df["skill_total"] = df["skill_id"].map(skill_totals)


#Total number of skill observations across the full analytical dataset.
global_skill_total = int(df["x_os"].sum())

df["global_skill_total"] = global_skill_total


#Calculates RCA as the occupation-level share of a skill divided by its global share.
df["rca"] = (
    (df["x_os"] / df["occupation_skill_total"]) / (df["skill_total"] / df["global_skill_total"])
)

def check_esco_confirmed(row):
    """Check whether an observed occupation-skill pair exists in the official ESCO data."""
    pair = (row["occupation_id"], row["skill_id"])
    return pair in official_pairs


def get_relation_type(row):
    """Return the official ESCO relation type for a pair when one is available."""
    pair = (row["occupation_id"], row["skill_id"])
    return official_relation_type.get(pair)


df["esco_confirmed"] = df.apply(check_esco_confirmed, axis=1)

df["esco_relation_type"] = df.apply(get_relation_type, axis=1)

#This sorts each occupation's skills from highest to lowest RCA.
df = df.sort_values(by=["occupation", "rca"], ascending=[True, False])

df.to_csv(OUTPUT_FILE, index=False, encoding="utf-8-sig")