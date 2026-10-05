import json
from collections import defaultdict

INPUT_FILE = "skillab_jobs_isco25_deduplicated.json"

with open(INPUT_FILE, "r", encoding="utf-8") as f:jobs = json.load(f)

occupation_support = defaultdict(set)

for job in jobs:
    job_id = job.get("id")

    for uri in job.get("occupations", []):
        if "/esco/occupation/" in uri:
            occupation_id = uri.split("/")[-1]
            occupation_support[occupation_id].add(job_id)

print(f"Total deduplicated jobs: {len(jobs)}")
print(f"Distinct ESCO occupations: {len(occupation_support)}")

support_counts = {
    occupation_id: len(job_ids)
    for occupation_id, job_ids in occupation_support.items()
}

print("Occupations with support >= 5:", sum(1 for support in support_counts.values() if support >= 5))
print("\nTop occupations by support:")

for occupation_id, support in sorted(
    support_counts.items(),
    key=lambda x: x[1],
    reverse=True
)[:20]:
    print(occupation_id, support)