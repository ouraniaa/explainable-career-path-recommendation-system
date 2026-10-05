import csv

OCCUPATIONS_FILE = "occupations_en.csv"

names_to_check = {
    "missionary",
    "data scientist",
    "cloud DevOps engineer",
    "ICT system administrator",
    "software developer"
}

with open(OCCUPATIONS_FILE, "r", encoding="utf-8") as f:
    reader = csv.DictReader(f)

    for row in reader:
        name = row.get("preferredLabel", "")
        isco_group = row.get("iscoGroup", "")
        uri = row.get("conceptUri", "")

        if name in names_to_check:
            print(f"{name}")
            print(f"  iscoGroup: {isco_group}")
            print(f"  conceptUri: {uri}")
            print()