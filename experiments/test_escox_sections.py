import json
from esco_skill_extractor import SkillExtractor

JOB_ID = 5319595
JSON_FILE = "skillab_jobs_isco25.json"
THRESHOLD = 0.60

with open(JSON_FILE, "r", encoding="utf-8") as f:
    jobs = json.load(f)

job = next(
    j for j in jobs
    if j.get("id") == JOB_ID
)

description = job.get("description", "")

print("=" * 80)
print("JOB")
print("=" * 80)
print("ID:", JOB_ID)
print("Title:", job.get("title"))

marker = "The position"

if marker in description:
    position_only = description.split(marker, 1)[1]
else:
    position_only = description


print("\nFull description length:", len(description))
print("Position-only length:", len(position_only))


extractor = SkillExtractor(skills_threshold=THRESHOLD)

print("\n" + "=" * 80)
print("FULL DESCRIPTION")
print("=" * 80)

full_result = extractor.get_skills([description])
full_skills = full_result[0]

print(f"Extracted skills: {len(full_skills)}")

for skill in full_skills:
    print("-", skill)

print("\n" + "=" * 80)
print("POSITION-ONLY DESCRIPTION")
print("=" * 80)

position_result = extractor.get_skills([position_only])
position_skills = position_result[0]

print(f"Extracted skills: {len(position_skills)}")

for skill in position_skills:
    print("-", skill)


full_set = set(full_skills)
position_set = set(position_skills)

removed = full_set - position_set
remaining = full_set & position_set
new_skills = position_set - full_set

print("\n" + "=" * 80)
print("COMPARISON")
print("=" * 80)

print("\nSkills removed when using position-only text:")
for skill in sorted(removed):
    print("-", skill)

print("\nSkills remaining in both:")
for skill in sorted(remaining):
    print("-", skill)

print("\nSkills appearing only in position-only extraction:")
for skill in sorted(new_skills):
    print("-", skill)