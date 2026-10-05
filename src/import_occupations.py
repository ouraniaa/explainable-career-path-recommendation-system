"""
Imports ESCO occupations into the Neo4j knowledge graph.

This file exists to make sure the occupation nodes required by the analytical
scope are present in Neo4j before recommendation and graph-based modules use them.
It reads the processed occupation data, creates one node per ESCO occupation, and
stores the identifiers and labels needed by the rest of the system.

Keeping this import step separate also makes it easier to rebuild or refresh the
occupation part of the graph without changing the recommendation logic.
"""

import csv
import json
import os

from dotenv import load_dotenv
from neo4j import GraphDatabase

load_dotenv()

URI = os.getenv("NEO4J_URI")
USERNAME = os.getenv("NEO4J_USER")
PASSWORD = os.getenv("NEO4J_PASSWORD")

if not URI or not USERNAME or not PASSWORD:
    raise RuntimeError("Neo4j environment variables are required.")

AUTH = (USERNAME, PASSWORD)
JSON_FILE = "skillab_jobs_isco25.json"
OCCUPATIONS_FILE = "occupations_en.csv"

def extract_esco_occupation_id(uri: str):
    if not uri:
        return None
    if "/esco/occupation/" not in uri:
        return None

    return uri.split("/")[-1]

def create_occupation_relationships(tx, batch):
    query = """
    UNWIND $batch AS row
    MATCH (j:JobPosting {job_id: row.job_id})
    MERGE (o:Occupation {esco_id: row.occupation_id})
    MERGE (j)-[:BELONGS_TO]->(o)
    """

    tx.run(query, batch=batch)

def enrich_occupation_names(tx, batch):
    query = """
    UNWIND $batch AS occupation_data

    MATCH (o:Occupation {esco_id: occupation_data.occupation_id})

    SET o.name = occupation_data.occupation_name,
        o.isco_group = occupation_data.isco_group
    """

    tx.run(query, batch=batch)


def import_occupations():
    print("Reading Skillab JSON...")

    with open(JSON_FILE, "r", encoding="utf-8") as f:
        jobs = json.load(f)

    rows = []

    for job in jobs:
        job_id = job.get("id")
        occupations = job.get("occupations", [])

        if not job_id:
            continue

        for occupation_uri in occupations:
            occupation_id = extract_esco_occupation_id(occupation_uri)

            if occupation_id:
                rows.append({
                    "job_id": job_id,
                    "occupation_id": occupation_id
                })

    print(f"{len(rows)} JobPosting-Occupation mappings were found .")

    batch_size = 1000

    with GraphDatabase.driver(URI, auth=AUTH) as driver:
        with driver.session() as session:
            for i in range(0, len(rows), batch_size):
                batch = rows[i:i + batch_size]

                session.execute_write(
                    create_occupation_relationships,
                    batch
                )

    print("The creation of Occupation nodes and BELONGS_TO relationships has been completed.")


def enrich_occupations():
    print("Reading ESCO occupations CSV...")

    occupations_mapping = []

    with open(OCCUPATIONS_FILE, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        for row in reader:
            uri = row.get("conceptUri", "")
            preferred_label = row.get("preferredLabel", "")
            isco_group = str(row.get("iscoGroup", "")).strip()

            if not uri or not preferred_label:
                continue

            if "/esco/occupation/" not in uri:
                continue

            occupation_id = uri.split("/")[-1]

            occupations_mapping.append({
                "occupation_id": occupation_id,
                "occupation_name": preferred_label,
                "isco_group": isco_group
            })

    print(
        f"{len(occupations_mapping)} occupations were found"
        f"in ESCO occupations CSV."
    )

    batch_size = 1000

    with GraphDatabase.driver(URI, auth=AUTH) as driver:
        with driver.session() as session:
            for i in range(0, len(occupations_mapping), batch_size):
                batch = occupations_mapping[i:i + batch_size]

                session.execute_write(
                    enrich_occupation_names,
                    batch
                )

    print("The enrichment of Occupation nodes was completed successfully.")


if __name__ == "__main__":
    import_occupations()
    enrich_occupations()