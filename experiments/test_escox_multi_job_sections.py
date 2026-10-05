import json

from esco_skill_extractor import SkillExtractor

JSON_FILE = "skillab_jobs_isco25.json"
THRESHOLD = 0.60

JOB_IDS = [
    5319595,  #IT Technician - Telephony - M/F
    155039,   #Business Demand Expert...
    102260,   #IT Operations Manager
    93532,    #Dev Sec Ops Engineer(s)
    164800    #Master Data Management Specialist
]

#Load jobs
with open(JSON_FILE, "r", encoding="utf-8") as f:
    jobs = json.load(f)

jobs_by_id = {
    job.get("id"): job
    for job in jobs
}


#Helper: try to isolate job-relevant text
SECTION_MARKERS = [
    "The position",
    "The Position",
    "Your role",
    "Your Role",
    "The role",
    "The Role",
    "Responsibilities",
    "Main responsibilities",
    "Main missions",
    "Your responsibilities",
    "Job description",
    "Job Description",
    "What you'll do",
    "What you will do",
    "Profile sought",
    "Requirements"
]


def extract_job_section(description: str):
    if not description:
        return "", None

    matches = []

    for marker in SECTION_MARKERS:
        index = description.find(marker)

        if index != -1:
            matches.append((index, marker))

    if not matches:
        return description, None

    index, marker = min(matches, key=lambda x: x[0])

    return description[index:], marker


#Initialize extractor once
extractor = SkillExtractor(skills_threshold=THRESHOLD)


#Run experiment
for job_id in JOB_IDS:
    job = jobs_by_id.get(job_id)

    if not job:
        print(f"\nJob {job_id} not found.")
        continue

    title = job.get("title", "")
    description = job.get("description", "")

    focused_description, marker = extract_job_section(description)

    print("\n")
    print("=" * 100)
    print(f"JOB ID: {job_id}")
    print(f"TITLE: {title}")
    print("=" * 100)

    print(f"Full description length: {len(description)}")
    print(f"Focused description length: {len(focused_description)}")
    print(f"Detected marker: {marker}")

    #Full description
    full_result = extractor.get_skills([description])
    full_skills = set(full_result[0])

    #Focused description
    focused_result = extractor.get_skills([focused_description])
    focused_skills = set(focused_result[0])

    removed = full_skills - focused_skills
    remaining = full_skills & focused_skills
    added = focused_skills - full_skills

    print("\nFULL DESCRIPTION")
    print(f"Skills: {len(full_skills)}")

    for skill in sorted(full_skills):
        print("-", skill)

    print("\nFOCUSED DESCRIPTION")
    print(f"Skills: {len(focused_skills)}")

    for skill in sorted(focused_skills):
        print("-", skill)

    print("\nREMOVED AFTER TRIMMING")
    print(f"Skills removed: {len(removed)}")

    for skill in sorted(removed):
        print("-", skill)

    print("\nREMAINING IN BOTH")
    print(f"Skills remaining: {len(remaining)}")

    for skill in sorted(remaining):
        print("-", skill)

    print("\nONLY IN FOCUSED VERSION")
    print(f"New skills: {len(added)}")

    for skill in sorted(added):
        print("-", skill)