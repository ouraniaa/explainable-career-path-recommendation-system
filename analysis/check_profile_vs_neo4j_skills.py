import pandas as pd
import os
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()

PROFILE_FILE = "data/processed/occupation_skill_profiles.csv"

URI = os.getenv("NEO4J_URI")
USER = os.getenv("NEO4J_USER")
PASSWORD = os.getenv("NEO4J_PASSWORD")

if not URI or not USER or not PASSWORD:
    raise RuntimeError("Neo4j environment variables are required.")

#Load skills from occupation_skill_profiles.csv
df = pd.read_csv(PROFILE_FILE)

profile_skills = (
    df[["skill_id", "skill_name"]]
    .dropna(subset=["skill_id"])
    .drop_duplicates(subset=["skill_id"])
)

profile_ids = set(profile_skills["skill_id"])

print("Distinct skills in occupation_skill_profiles.csv:", len(profile_ids))


#Load skills from Neo4j
driver = GraphDatabase.driver(
    URI,
    auth=(USER, PASSWORD)
)

with driver.session() as session:
    result = session.run("""
        MATCH (s:Skill)
        RETURN s.esco_id AS skill_id,
               s.name AS skill_name
    """)

    neo4j_skills = [
        {
            "skill_id": record["skill_id"],
            "skill_name": record["skill_name"]
        }
        for record in result
    ]

driver.close()

neo4j_df = pd.DataFrame(neo4j_skills)

neo4j_ids = set(
    neo4j_df["skill_id"]
    .dropna()
)

print("Distinct Skill nodes in Neo4j:", len(neo4j_ids))

only_in_profile = profile_ids - neo4j_ids
only_in_neo4j = neo4j_ids - profile_ids
common = profile_ids & neo4j_ids

print("\n" + "=" * 80)
print("COMPARISON")
print("=" * 80)

print("Common skills:", len(common))
print("Only in occupation_skill_profiles.csv:", len(only_in_profile))
print("Only in Neo4j:", len(only_in_neo4j))

if only_in_profile:
    print("\n" + "=" * 80)
    print("EXAMPLES: SKILLS IN PROFILE BUT NOT IN NEO4J")
    print("=" * 80)

    examples = profile_skills[profile_skills["skill_id"].isin(only_in_profile)].head(30)

    print(examples.to_string(index=False))


if only_in_neo4j:
    print("\n" + "=" * 80)
    print("EXAMPLES: SKILLS IN NEO4J BUT NOT IN PROFILE")
    print("=" * 80)

    examples = neo4j_df[neo4j_df["skill_id"].isin(only_in_neo4j)].head(30)

    print(examples.to_string(index=False))


print("\n" + "=" * 80)
print("SOURCE TYPES OF PROFILE-ONLY SKILLS")
print("=" * 80)

profile_only_rows = df[df["skill_id"].isin(only_in_profile)]

print(profile_only_rows["source_type"].value_counts().to_string())

print("\nESCO RELATION TYPES OF PROFILE-ONLY SKILLS")
print(profile_only_rows["esco_relation_type"].value_counts(dropna=False).to_string())

unique_profile_only = (
    profile_only_rows[["skill_id", "skill_name"]]
    .drop_duplicates(subset=["skill_id"])
)

print("\n" + "=" * 80)
print("UNIQUE PROFILE-ONLY ESCO SKILLS")
print("=" * 80)

print("Unique missing skills:", len(unique_profile_only))

print(unique_profile_only.sort_values("skill_name").head(50).to_string(index=False))