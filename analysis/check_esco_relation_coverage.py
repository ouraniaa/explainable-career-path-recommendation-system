import pandas as pd
import os
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
    """
    Converts:
    http://data.europa.eu/esco/skill/xxxx
    or
    http://data.europa.eu/esco/occupation/xxxx

    into:
    xxxx
    """
    if pd.isna(uri):
        return ""

    return str(uri).rstrip("/").split("/")[-1]


#Load official ESCO occupation-skill relations
df = pd.read_csv(CSV_FILE)

df["occupation_id"] = df["occupationUri"].apply(extract_uuid)
df["skill_id"] = df["skillUri"].apply(extract_uuid)

official_occupation_ids = set(df["occupation_id"])
official_skill_ids = set(df["skill_id"])

print("=" * 80)
print("OFFICIAL ESCO DATA")
print("=" * 80)

print(f"Official relations: {len(df)}")
print(f"Distinct occupations in official relations: {len(official_occupation_ids)}")
print(f"Distinct skills in official relations: {len(official_skill_ids)}")


driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))


with driver.session() as session:
    occupation_records = session.run(
        """
        MATCH (o:Occupation)
        WHERE o.esco_id IS NOT NULL
        RETURN o.esco_id AS id, o.name AS name
        """
    )

    graph_occupations = {
        record["id"]: record["name"]
        for record in occupation_records
    }

    skill_records = session.run(
        """
        MATCH (s:Skill)
        WHERE s.esco_id IS NOT NULL
        RETURN s.esco_id AS id, s.name AS name
        """
    )

    graph_skills = {
        record["id"]: record["name"]
        for record in skill_records
    }


driver.close()

graph_occupation_ids = set(graph_occupations.keys())
graph_skill_ids = set(graph_skills.keys())


matched_occupations = graph_occupation_ids & official_occupation_ids
unmatched_occupations = graph_occupation_ids - official_occupation_ids

print("\n")
print("=" * 80)
print("OCCUPATION COVERAGE")
print("=" * 80)

print(f"Neo4j occupations: {len(graph_occupation_ids)}")
print(f"Matched occupations: {len(matched_occupations)}")
print(f"Unmatched occupations: {len(unmatched_occupations)}")

if graph_occupation_ids:
    occupation_coverage = (len(matched_occupations) / len(graph_occupation_ids)) * 100

    print(f"Occupation coverage: {occupation_coverage:.2f}%")


matched_skills = graph_skill_ids & official_skill_ids
unmatched_skills = graph_skill_ids - official_skill_ids

print("\n")
print("=" * 80)
print("SKILL COVERAGE")
print("=" * 80)

print(f"Neo4j skills: {len(graph_skill_ids)}")
print(f"Matched skills: {len(matched_skills)}")
print(f"Unmatched skills: {len(unmatched_skills)}")

if graph_skill_ids:
    skill_coverage = (len(matched_skills) / len(graph_skill_ids)) * 100

    print(f"Skill coverage: {skill_coverage:.2f}%")


#Relations where BOTH nodes exist in our graph
usable_relations = df[
    df["occupation_id"].isin(graph_occupation_ids)
    & df["skill_id"].isin(graph_skill_ids)
].copy()

print("\n")
print("=" * 80)
print("USABLE OFFICIAL RELATIONS")
print("=" * 80)

print("Official ESCO relations where both Occupation and Skill "
    f"exist in Neo4j: {len(usable_relations)}"
)

print("Distinct graph occupations with at least one usable official relation:",
    usable_relations["occupation_id"].nunique()
)

print("Distinct graph skills participating in usable official relations:",
    usable_relations["skill_id"].nunique()
)

#Essential vs optional
print("\n")
print("=" * 80)
print("RELATION TYPE DISTRIBUTION")
print("=" * 80)
print(usable_relations["relationType"].value_counts(dropna=False).to_string())

#Show unmatched examples
print("\n")
print("=" * 80)
print("EXAMPLE UNMATCHED OCCUPATIONS")
print("=" * 80)

for occupation_id in list(unmatched_occupations)[:10]:
    print(occupation_id, "->", graph_occupations.get(occupation_id))


print("\n")
print("=" * 80)
print("EXAMPLE UNMATCHED SKILLS")
print("=" * 80)

for skill_id in list(unmatched_skills)[:10]:
    print(skill_id, "->", graph_skills.get(skill_id))