"""
Removes duplicate job postings before the labor-market analysis is performed.

This file was created because the raw Skillab job dataset contained repeated postings.
Keeping those duplicates would artificially increase the frequency of some occupations
and skills, which could distort the later RCA calculations and market-based evidence.

Two postings are treated as duplicates when they have the same normalized title and
description. Records with a missing title or description are kept so potentially useful
data is not removed just because one of those fields is incomplete.
"""
import json

INPUT_FILE = "skillab_jobs_isco25.json"
OUTPUT_FILE = "skillab_jobs_isco25_deduplicated.json"

with open(INPUT_FILE, "r", encoding="utf-8") as f:
    jobs = json.load(f)

seen = set()
deduplicated_jobs = []

for job in jobs:
    title = job.get("title")
    description = job.get("description")

    if not title or not description:
        deduplicated_jobs.append(job)
        continue

    key = (
        title.strip().lower(),
        description.strip()
    )

    if key not in seen:
        seen.add(key)
        deduplicated_jobs.append(job)

print(f"Original jobs: {len(jobs)}")
print(f"Deduplicated jobs: {len(deduplicated_jobs)}")
print(f"Removed duplicates: {len(jobs) - len(deduplicated_jobs)}")

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(
        deduplicated_jobs,
        f,
        ensure_ascii=False,
        indent=2
    )

print(f"\nSaved to: {OUTPUT_FILE}")