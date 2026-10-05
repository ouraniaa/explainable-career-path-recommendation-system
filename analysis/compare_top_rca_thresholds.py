import pandas as pd

INPUT_FILE = "full_rca_diagnostic.csv"

OCCUPATIONS = [
    "data scientist",
    "cloud DevOps engineer",
    "ICT system administrator",
    "ICT application configurator",
    "software developer"
]

THRESHOLDS = [1, 2, 3]
TOP_N = 10

#Load RCA table
df = pd.read_csv(INPUT_FILE)

def print_top_skills(occupation_name, threshold):

    subset = df[
        (df["occupation"] == occupation_name)
        & (df["x_os"] >= threshold)
    ].copy()

    subset = subset.sort_values(by="rca", ascending=False)

    top = subset.head(TOP_N)

    print("\n")
    print("=" * 100)
    print(
        f"{occupation_name.upper()} | "
        f"x_os >= {threshold}"
    )
    print("=" * 100)

    print(f"Eligible pairs: {len(subset)}")

    if top.empty:
        print("No skills available.")
        return

    for _, row in top.iterrows():
        relation_type = row["esco_relation_type"]

        if pd.isna(relation_type):
            relation_type = "-"

        print(
            f"{row['skill']} | "
            f"x_os={int(row['x_os'])} | "
            f"skill_total={int(row['skill_total'])} | "
            f"RCA={row['rca']:.2f} | "
            f"ESCO={bool(row['esco_confirmed'])} | "
            f"type={relation_type}"
        )

for occupation in OCCUPATIONS:

    print("\n\n")
    print("#" * 100)
    print(f"OCCUPATION: {occupation}")
    print("#" * 100)

    for threshold in THRESHOLDS:
        print_top_skills(
            occupation,
            threshold
        )