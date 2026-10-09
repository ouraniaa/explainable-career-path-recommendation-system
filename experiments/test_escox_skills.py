import json

from esco_skill_extractor import SkillExtractor

JOB_ID = 5319595
JSON_FILE = "skillab_jobs_isco25.json"

THRESHOLDS = [0.55, 0.60, 0.65, 0.70]

with open(JSON_FILE, "r", encoding="utf-8") as f:
    jobs = json.load(f)

job = next(
    j for j in jobs
    if j.get("id") == JOB_ID
)

title = job.get("title", "")
description = job.get("description", "")

print("=" * 80)
print("JOB")
print("=" * 80)

print("ID:", JOB_ID)
print("Title:", title)

print("\nOriginal Skillab skills:")
for skill in job.get("skills", []):
    print("-", skill)


for threshold in THRESHOLDS:
    print("\n" + "=" * 80)
    print(f"SKILL THRESHOLD = {threshold}")
    print("=" * 80)

    extractor = SkillExtractor(skills_threshold=threshold)

    result = extractor.get_skills([description])

    extracted_skills = result[0]

    print(
        f"Extracted skills: "
        f"{len(extracted_skills)}"
    )

    for skill in extracted_skills:
        print("-", skill)