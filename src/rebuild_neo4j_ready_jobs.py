import json

INPUT_FILE = "skillab_jobs_isco25.json"
OUTPUT_FILE = "neo4j_ready_jobs_fixed.json"

with open(INPUT_FILE, "r", encoding="utf-8") as f:
    jobs = json.load(f)

neo4j_jobs = []

for job in jobs:
    skill_ids = []

    for skill_uri in job.get("skills", []):
        if "/esco/skill/" in skill_uri:
            skill_id = skill_uri.split("/")[-1]
            skill_ids.append(skill_id)

    neo4j_jobs.append({
        "job_id": job.get("id"),
        "title": job.get("title"),
        "skills": skill_ids
    })

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(
        neo4j_jobs,
        f,
        ensure_ascii=False,
        indent=2
    )