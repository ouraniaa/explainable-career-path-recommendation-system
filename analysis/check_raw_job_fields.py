import json

with open("skillab_jobs_isco25.json", "r", encoding="utf-8") as f:
    jobs = json.load(f)

job = next(j for j in jobs if j.get("id") == 5319595)

print("Fields:")
for key in job.keys():
    print("-", key)