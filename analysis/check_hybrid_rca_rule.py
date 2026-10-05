import pandas as pd

INPUT_FILE = "full_rca_diagnostic.csv"

df = pd.read_csv(INPUT_FILE)

#Hybrid rule
#Keep pair if: ESCO confirmed == True OR x_os >= 3
df["hybrid_keep"] = (
    (df["esco_confirmed"] == True)
    | (df["x_os"] >= 3)
)

#Summary per occupation
summary = (
    df.groupby("occupation")
    .agg(
        OriginalPairs=("skill", "count"),
        RetainedPairs=("hybrid_keep", "sum")
    )
    .reset_index()
)

summary["RetentionPercent"] = (summary["RetainedPairs"] / summary["OriginalPairs"] * 100)

print("=" * 100)
print("HYBRID RULE SUMMARY")
print("Rule: ESCO confirmed = True OR x_os >= 3")
print("=" * 100)

print(
    summary.sort_values(
        by="RetainedPairs",
        ascending=True
    ).to_string(
        index=False,
        formatters={
            "RetentionPercent": lambda x: f"{x:.2f}%"
        }
    )
)


total_original = len(df)
total_retained = int(df["hybrid_keep"].sum())

print("\n")
print("=" * 100)
print("OVERALL RETENTION")
print("=" * 100)

print(f"Original pairs: {total_original}")
print(f"Retained pairs: {total_retained}")
print(f"Removed pairs: {total_original - total_retained}")
print(
    f"Retention: "
    f"{total_retained / total_original * 100:.2f}%"
)


#Smallest occupations after filtering
print("\n")
print("=" * 100)
print("OCCUPATIONS WITH FEWEST RETAINED SKILLS")
print("=" * 100)

print(
    summary.sort_values(
        by="RetainedPairs",
        ascending=True
    ).head(15).to_string(
        index=False,
        formatters={
            "RetentionPercent": lambda x: f"{x:.2f}%"
        }
    )
)


#Inspect representative occupations
occupations_to_check = [
    "data scientist",
    "cloud DevOps engineer",
    "ICT system administrator",
    "ICT application configurator",
    "software developer"
]


for occupation in occupations_to_check:

    subset = df[
        (df["occupation"] == occupation)
        & (df["hybrid_keep"])
    ].copy()

    subset = subset.sort_values(
        by="rca",
        ascending=False
    )

    print("\n")
    print("=" * 100)
    print(f"{occupation.upper()} — RETAINED TOP RCA SKILLS")
    print("=" * 100)

    print(f"Retained skills: {len(subset)}")

    if subset.empty:
        print("No retained skills.")
        continue

    for _, row in subset.head(15).iterrows():

        relation_type = row["esco_relation_type"]

        if pd.isna(relation_type):
            relation_type = "-"

        print(
            f"{row['skill']} | "
            f"x_os={int(row['x_os'])} | "
            f"RCA={row['rca']:.2f} | "
            f"ESCO={bool(row['esco_confirmed'])} | "
            f"type={relation_type}"
        )


#Known suspicious skills that survive
suspicious_skills = [
    "gender studies",
    "recreation activities",
    "oversee operational safety on trains",
    "tend to elderly people",
    "prepare fishing equipment",
    "child psychiatry"
]

surviving_suspicious = df[
    (df["skill"].isin(suspicious_skills))
    & (df["hybrid_keep"])
].sort_values(by="rca", ascending=False)


print("\n")
print("=" * 100)
print("SUSPICIOUS PAIRS SURVIVING HYBRID RULE")
print("=" * 100)

if surviving_suspicious.empty:
    print("None.")

else:
    for _, row in surviving_suspicious.iterrows():
        print(
            f"{row['occupation']} "
            f"→ {row['skill']} | "
            f"x_os={int(row['x_os'])} | "
            f"RCA={row['rca']:.2f} | "
            f"ESCO={bool(row['esco_confirmed'])}"
        )