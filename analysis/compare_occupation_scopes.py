import json
import csv
from collections import defaultdict

JOBS_FILE = "skillab_jobs_isco25_deduplicated.json"
OCCUPATIONS_FILE = "occupations_en.csv"

#Load deduplicated jobs
with open(JOBS_FILE, "r", encoding="utf-8") as f:
    jobs = json.load(f)

#Load ESCO occupation metadata
occupation_info = {}

with open(OCCUPATIONS_FILE, "r", encoding="utf-8-sig") as f:
    reader = csv.DictReader(f)

    for row in reader:
        uri = row.get("conceptUri", "")
        name = row.get("preferredLabel", "")
        isco_group = str(row.get("iscoGroup", "")).strip()

        if "/esco/occupation/" not in uri:
            continue

        occupation_id = uri.split("/")[-1]

        occupation_info[occupation_id] = {
            "name": name,
            "isco_group": isco_group
        }

#Calculate support per occupation
occupation_jobs = defaultdict(set)

for job in jobs:
    job_id = job.get("id")

    for uri in job.get("occupations", []):
        if "/esco/occupation/" not in uri:
            continue

        occupation_id = uri.split("/")[-1]
        occupation_jobs[occupation_id].add(job_id)

#Helper function for testing a domain
def analyze_domain(name, condition):
    valid_occupations = []

    for occupation_id, job_ids in occupation_jobs.items():
        info = occupation_info.get(occupation_id)

        if not info:
            continue

        isco_group = info["isco_group"]
        support = len(job_ids)

        if condition(isco_group) and support >= 5:
            valid_occupations.append(occupation_id)

    covered_jobs = set()

    for occupation_id in valid_occupations:
        covered_jobs.update(occupation_jobs[occupation_id])

    print(f"\n{name}")
    print("-" * 40)
    print(f"Occupations: {len(valid_occupations)}")
    print(f"Covered jobs: {len(covered_jobs)}")
    print(f"Total jobs: {len(jobs)}")
    print(
        f"Coverage: "
        f"{100 * len(covered_jobs) / len(jobs):.2f}%"
    )


#Compare domains
analyze_domain(
    "25xx only",
    lambda g: g.startswith("25")
)

analyze_domain(
    "25xx + 35xx",
    lambda g:
        g.startswith("25")
        or g.startswith("35")
)

analyze_domain(
    "25xx + 1330",
    lambda g:
        g.startswith("25")
        or g == "1330"
)

analyze_domain(
    "25xx + 35xx + 1330",
    lambda g:
        g.startswith("25")
        or g.startswith("35")
        or g == "1330"
)