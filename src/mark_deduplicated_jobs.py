"""
Marks the deduplicated job postings inside Neo4j so later analysis uses the cleaned dataset.

This file was created after duplicate postings were identified in the raw Skillab data.
Removing duplicates in a separate preprocessing step was not enough on its own, because
the Neo4j graph still needed a clear way to distinguish the cleaned postings from the
original imported records.

The script matches the deduplicated job IDs back to their JobPosting nodes and marks them
accordingly. This allows later RCA and market-analysis queries to work only with the
deduplicated postings and avoids duplicate jobs influencing occupation or skill frequencies.
"""
import json
import os

from dotenv import load_dotenv
from neo4j import GraphDatabase

load_dotenv()

JSON_FILE = "skillab_jobs_isco25_deduplicated.json"

URI = os.getenv("NEO4J_URI")
USERNAME = os.getenv("NEO4J_USER")
PASSWORD = os.getenv("NEO4J_PASSWORD")

if not URI or not USERNAME or not PASSWORD:
    raise RuntimeError("Neo4j environment variables are required.")

#Load deduplicated job ids
with open(JSON_FILE, "r", encoding="utf-8") as f:
    jobs = json.load(f)

job_ids = [job["id"] for job in jobs]

driver = GraphDatabase.driver(URI, auth=(USERNAME, PASSWORD))

with driver.session() as session:
    session.run("""
        MATCH (j:JobPosting)
        SET j.is_deduplicated = false
    """)

    session.run("""
        UNWIND $job_ids AS job_id

        MATCH (j:JobPosting {job_id: job_id})

        SET j.is_deduplicated = true
    """, job_ids=job_ids)

driver.close()