import pandas as pd

INPUT_FILE = "occupation_skill_profiles.csv"

df = pd.read_csv(INPUT_FILE)

summary = (df.groupby(["occupation_id", "occupation_name"]).agg(
        TotalSkills=("skill_id", "count"),
        BothSkills=("source_type", lambda x: (x == "BOTH").sum()),
        EscoSkills=("has_esco_relation", "sum"),
        MarketSkills=("has_market_evidence", "sum")
    )
    .reset_index()
)

summary["BothAsPercentOfEsco"] = (summary["BothSkills"] / summary["EscoSkills"] * 100)

print("=" * 100)
print("BOTH COVERAGE PER OCCUPATION")
print("=" * 100)

print(
    summary.sort_values("BothSkills",ascending=True).to_string(index=False,formatters={"BothAsPercentOfEsco": lambda x: f"{x:.2f}%"})
)

print("\n")
print("=" * 100)
print("BOTH COUNT DISTRIBUTION")
print("=" * 100)

for threshold in [1, 2, 3, 5, 10, 15, 20]:
    count = (summary["BothSkills"] >= threshold).sum()

    print(
        f"BOTH >= {threshold}: "
        f"{count}/{len(summary)} occupations "
        f"({count / len(summary) * 100:.2f}%)"
    )

print("\n")
print("=" * 100)
print("SUMMARY")
print("=" * 100)
print(f"Min BOTH: {summary['BothSkills'].min()}")
print(f"Median BOTH: {summary['BothSkills'].median()}")
print(f"Mean BOTH: {summary['BothSkills'].mean():.2f}")
print(f"Max BOTH: {summary['BothSkills'].max()}")