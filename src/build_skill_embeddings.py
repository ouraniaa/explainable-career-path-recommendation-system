"""
Creates semantic embeddings for the canonical ESCO skills used by the system.

The script first finds the occupations that belong to the current analytical
scope, then loads their ESCO skills from Neo4j. After that, it creates one
embedding for each skill name using a SentenceTransformer model and saves the
results to disk.

The saved embeddings can then be reused by the recommendation system without
having to generate them again every time the application runs.
"""
import numpy as np
import pandas as pd
import os
from dotenv import load_dotenv
from neo4j import GraphDatabase
from sentence_transformers import SentenceTransformer

load_dotenv()

URI = os.getenv("NEO4J_URI")
USER = os.getenv("NEO4J_USER")
PASSWORD = os.getenv("NEO4J_PASSWORD")

if not URI or not USER or not PASSWORD:
    raise RuntimeError("Neo4j environment variables are required.")

PROFILE_FILE = "data/processed/occupation_skill_profiles.csv"
EMBEDDINGS_FILE = ("data/processed/skill_embeddings_mpnet.npy")
INDEX_FILE = ("data/processed/skill_embeddings_index.csv")
MODEL_NAME = ("sentence-transformers/all-mpnet-base-v2")

def load_analytical_occupation_ids():
    df = pd.read_csv(PROFILE_FILE)
    occupation_ids = (df["occupation_id"].dropna().drop_duplicates().tolist())

    return occupation_ids


def load_canonical_skills(session, occupation_ids):
    result = session.run("""
        MATCH (o:Occupation)-[:ESCO_REQUIRES]->(s:Skill)

        WHERE o.esco_id IN $occupation_ids
          AND s.esco_id IS NOT NULL
          AND s.name IS NOT NULL

        RETURN DISTINCT
            s.esco_id AS skill_id,
            s.name AS skill_name

        ORDER BY skill_id
    """,
        occupation_ids=occupation_ids
    )

    skills = []

    for record in result:
        skills.append({
            "skill_id": record["skill_id"],
            "skill_name": record["skill_name"]
        })

    return skills

def build_embeddings(skills):
    model = SentenceTransformer(MODEL_NAME)
    skill_names = [skill["skill_name"] for skill in skills]
    embeddings = model.encode(skill_names, normalize_embeddings=True, show_progress_bar=True)

    return embeddings

def save_embeddings(skills, embeddings):
    """
    Saves the generated embeddings and a small index file that connects each embedding row with the corresponding ESCO skill.
    """
    np.save(EMBEDDINGS_FILE, embeddings)

    index_rows = []

    for index, skill in enumerate(skills):
        index_rows.append({
            "embedding_index": index, 
            "skill_id": skill["skill_id"],
            "skill_name": skill["skill_name"]
        })

    index_df = pd.DataFrame(index_rows)
    index_df.to_csv(INDEX_FILE, index=False)


def main():
    occupation_ids = (load_analytical_occupation_ids())

    driver = GraphDatabase.driver(URI, auth=(USER, PASSWORD))

    with driver.session() as session:
        skills = load_canonical_skills(session, occupation_ids)

    driver.close()

    if not skills:
        print("\nNo canonical skills found.")
        return

    embeddings = build_embeddings(skills)
    save_embeddings(skills, embeddings)

if __name__ == "__main__":
    main()