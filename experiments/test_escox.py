import json
from esco_skill_extractor import SkillExtractor

with open("skillab_jobs_isco25.json", "r", encoding="utf-8") as f:
    jobs = json.load(f)

# Job postings we want to check
titles_to_test = [
    "DATA ARCHITECT H/F",
    "Senior Data Engineer (F/H/X)",
    "System and network administrator M/F",
    "Consultant·e Data Scientist & AI Engineer - Senior"
]

thresholds = [0.50, 0.55, 0.60, 0.65]

for title_to_test in titles_to_test:
    job = next(
        (j for j in jobs if j.get("title") == title_to_test),
        None
    )

    if job is None:
        print(f"\nΔεν βρέθηκε: {title_to_test}")
        continue

    print("\n" + "=" * 80)
    print("JOB TITLE:")
    print(job.get("title"))

    print("\nORIGINAL OCCUPATIONS FROM SKILLAB:")
    print(job.get("occupations", []))

    description = job.get("description", "")

    for threshold in thresholds:
        print(f"\n--- THRESHOLD {threshold} ---")

        extractor = SkillExtractor(occupation_threshold=threshold)

        result = extractor.get_occupations([description])

        print(result)