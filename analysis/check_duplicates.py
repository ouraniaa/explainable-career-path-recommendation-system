import json
from collections import defaultdict

JSON_FILE = "skillab_jobs_isco25.json"

with open(JSON_FILE, "r", encoding="utf-8") as f: jobs = json.load(f)

print(f"Total jobs: {len(jobs)}")

#1. Duplicates based on source + source_id
source_id_groups = defaultdict(list)

for job in jobs:
    source = job.get("source")
    source_id = job.get("source_id")

    if source_id:
        key = (source, source_id)
        source_id_groups[key].append(job)

duplicate_source_ids = {
    key: group
    for key, group in source_id_groups.items()
    if len(group) > 1
}

print("\n=== DUPLICATES BY source + source_id ===")
print(f"Duplicate groups: {len(duplicate_source_ids)}")

for (source, source_id), group in duplicate_source_ids.items():
    print(f"\nSource: {source}")
    print(f"Source ID: {source_id}")

    for job in group:
        print(f"  id={job.get('id')} | title={job.get('title')}")

#2. Exact duplicate descriptions
description_groups = defaultdict(list)

for job in jobs:
    description = job.get("description")

    if description:
        normalized_description = description.strip()
        description_groups[normalized_description].append(job)

duplicate_descriptions = {
    description: group
    for description, group in description_groups.items()
    if len(group) > 1
}

print("\n=== DUPLICATES BY EXACT DESCRIPTION ===")
print(f"Duplicate groups: {len(duplicate_descriptions)}")

for description, group in duplicate_descriptions.items():
    print("\n--- Group ---")

    for job in group:
        print(
            f"id={job.get('id')} | "
            f"title={job.get('title')} | "
            f"source_id={job.get('source_id')}"
        )


#3. Exact duplicate title + description
title_description_groups = defaultdict(list)

for job in jobs:
    title = job.get("title")
    description = job.get("description")

    if title and description:
        key = (
            title.strip().lower(),
            description.strip()
        )
        title_description_groups[key].append(job)

duplicate_title_descriptions = {
    key: group
    for key, group in title_description_groups.items()
    if len(group) > 1
}

print("\n=== DUPLICATES BY TITLE + DESCRIPTION ===")
print(f"Duplicate groups: {len(duplicate_title_descriptions)}")

for (title, description), group in duplicate_title_descriptions.items():
    print(f"\nTitle: {title}")

    for job in group:
        print(
            f"  id={job.get('id')} | "
            f"source={job.get('source')} | "
            f"source_id={job.get('source_id')}"
        )

    total_jobs = len(jobs)

#Unique based on source + source_id
source_unique_keys = set()

for job in jobs:
    source = job.get("source")
    source_id = job.get("source_id")

    if source_id:
        source_unique_keys.add((source, source_id))
    else:
        #If source_id is missing, preserve the job as unique
        source_unique_keys.add(("missing", job.get("id")))


#Unique based on normalized title + exact description
title_description_unique_keys = set()

for job in jobs:
    title = job.get("title")
    description = job.get("description")

    if title and description:
        key = (
            title.strip().lower(),
            description.strip()
        )
    else:
        #Preserve incomplete records as unique
        key = ("missing", job.get("id"))

    title_description_unique_keys.add(key)


print("\n SUMMARY")

print(f"Original jobs: {total_jobs}")

print(
    f"Unique by source + source_id: "
    f"{len(source_unique_keys)}"
)

print(
    f"Would remove by source + source_id: "
    f"{total_jobs - len(source_unique_keys)}"
)

print(
    f"Unique by exact title + description: "
    f"{len(title_description_unique_keys)}"
)

print(
    f"Would remove by exact title + description: "
    f"{total_jobs - len(title_description_unique_keys)}"
)

from collections import Counter

group_sizes = Counter(
    len(group)
    for group in duplicate_title_descriptions.values()
)

print("\n DUPLICATE GROUP SIZE DISTRIBUTION")

for size, number_of_groups in sorted(group_sizes.items()):
    print(
        f"Groups with {size} records: "
        f"{number_of_groups}"
    )

largest_groups = sorted(
    duplicate_title_descriptions.items(),
    key=lambda x: len(x[1]),
    reverse=True
)

print("\n LARGEST DUPLICATE GROUPS ")

for (title, description), group in largest_groups[:10]:
    print("\n")
    print(f"Title: {title}")
    print(f"Group size: {len(group)}")

    for job in group:
        print(
            f"id={job.get('id')} | "
            f"source={job.get('source')} | "
            f"source_id={job.get('source_id')}"
        )