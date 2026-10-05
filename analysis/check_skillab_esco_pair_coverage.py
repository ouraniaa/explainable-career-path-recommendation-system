import os
import pandas as pd

from dotenv import load_dotenv
from neo4j import GraphDatabase

load_dotenv()

CSV_FILE = "occupationSkillRelations_en.csv"

NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USER = os.getenv("NEO4J_USER")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")

if not NEO4J_URI or not NEO4J_USER or not NEO4J_PASSWORD:
    raise RuntimeError("Neo4j environment variables are required.")

def extract_uuid(uri: str) -> str:
    if pd.isna(uri):
        return ""

    return str(uri).rstrip("/").split("/")[-1]


#Load official ESCO relations
df_esco = pd.read_csv(CSV_FILE)

df_esco["occupation_id"] = df_esco["occupationUri"].apply(extract_uuid)
df_esco["skill_id"] = df_esco["skillUri"].apply(extract_uuid)

official_pairs = set(zip(df_esco["occupation_id"], df_esco["skill_id"]))

official_relation_type = {(row["occupation_id"], row["skill_id"]): row["relationType"]
    for _, row in df_esco.iterrows()
}

#Read Skillab-derived occupation-skill pairs from Neo4j
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
    count(DISTINCT j) AS x_os

RETURN
    o.esco_id AS occupation_id,
    o.name AS occupation,
    s.esco_id AS skill_id,
    s.name AS skill,
    x_os
"""
with driver.session() as session:
    records = list(session.run(query))

driver.close()

rows = []

for record in records:

    occupation_id = record["occupation_id"]
    skill_id = record["skill_id"]

    pair = (occupation_id, skill_id)

    is_confirmed = pair in official_pairs

    rows.append({
        "occupation_id": occupation_id,
        "occupation": record["occupation"],
        "skill_id": skill_id,
        "skill": record["skill"],
        "x_os": record["x_os"],
        "esco_confirmed": is_confirmed,
        "esco_relation_type": (
            official_relation_type.get(pair)
            if is_confirmed
            else None
        )
    })

df = pd.DataFrame(rows)

#Overall pair coverage
total_pairs = len(df)

confirmed_pairs = int(df["esco_confirmed"].sum())
not_confirmed_pairs = total_pairs - confirmed_pairs

confirmed_percentage = (confirmed_pairs / total_pairs * 100
    if total_pairs > 0
    else 0
)


print("=" * 90)
print("OVERALL SKILLAB → ESCO PAIR COVERAGE")
print("=" * 90)

print(f"Total Skillab occupation-skill pairs: {total_pairs}")
print(f"ESCO-confirmed pairs: {confirmed_pairs}")
print(f"Not ESCO-confirmed pairs: {not_confirmed_pairs}")
print(f"Confirmed percentage: {confirmed_percentage:.2f}%")


#Essential / optional among confirmed pairs
print("\n")
print("=" * 90)
print("CONFIRMED PAIR RELATION TYPES")
print("=" * 90)

confirmed_df = df[df["esco_confirmed"]]

if len(confirmed_df) > 0:
    print(
        confirmed_df["esco_relation_type"]
        .value_counts(dropna=False)
        .to_string()
    )


#Pair support analysis
print("\n")
print("=" * 90)
print("PAIR SUPPORT ANALYSIS")
print("=" * 90)

def print_support_group(label, subset):

    total = len(subset)

    if total == 0:
        print(f"{label}: no pairs")
        return

    confirmed = int(subset["esco_confirmed"].sum())
    not_confirmed = total - confirmed

    percentage = confirmed / total * 100

    print(
        f"{label}: "
        f"total={total}, "
        f"confirmed={confirmed}, "
        f"not_confirmed={not_confirmed}, "
        f"confirmed%={percentage:.2f}%"
    )


print_support_group("x_os = 1", df[df["x_os"] == 1])

print_support_group("x_os = 2", df[df["x_os"] == 2])

print_support_group("x_os >= 2", df[df["x_os"] >= 2])

print_support_group("x_os >= 3", df[df["x_os"] >= 3])

print_support_group("x_os >= 5", df[df["x_os"] >= 5])

#Known suspicious skills
suspicious_skills = [
    "gender studies",
    "recreation activities",
    "oversee operational safety on trains",
    "tend to elderly people",
    "prepare fishing equipment",
    "child psychiatry"
]

print("\n")
print("=" * 90)
print("KNOWN SUSPICIOUS SKILLS")
print("=" * 90)

suspicious_df = df[df["skill"].isin(suspicious_skills)].sort_values(
    by=["skill", "x_os"],
    ascending=[True, False]
)

if suspicious_df.empty:
    print("No suspicious skill pairs found.")

else:
    for _, row in suspicious_df.iterrows():
        print(
            f"{row['occupation']} "
            f"→ {row['skill']} | "
            f"x_os={row['x_os']} | "
            f"ESCO confirmed={row['esco_confirmed']} | "
            f"type={row['esco_relation_type']}"
        )


print("\n")
print("=" * 90)
print("TOP NOT ESCO-CONFIRMED PAIRS BY SUPPORT")
print("=" * 90)

not_confirmed_df = df[~df["esco_confirmed"]].sort_values(by="x_os", ascending=False)

for _, row in not_confirmed_df.head(30).iterrows():
    print(
        f"{row['occupation']} "
        f"→ {row['skill']} | "
        f"x_os={row['x_os']}"
    )

#Top confirmed pairs by support
print("\n")
print("=" * 90)
print("TOP ESCO-CONFIRMED PAIRS BY SUPPORT")
print("=" * 90)

confirmed_sorted_df = df[df["esco_confirmed"]].sort_values(by="x_os", ascending=False)

for _, row in confirmed_sorted_df.head(30).iterrows():
    print(
        f"{row['occupation']} "
        f"→ {row['skill']} | "
        f"x_os={row['x_os']} | "
        f"type={row['esco_relation_type']}"
    )


OUTPUT_FILE = "skillab_esco_pair_validation.csv"

df.to_csv(OUTPUT_FILE, index=False, encoding="utf-8-sig")

print("\n")
print("=" * 90)
print("OUTPUT")
print("=" * 90)

print(f"Detailed validation saved to: {OUTPUT_FILE}")