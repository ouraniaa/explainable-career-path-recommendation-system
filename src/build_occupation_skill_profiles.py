"""
Builds the unified occupation-skill profile used by the recommendation system.

The script combines official ESCO occupation-skill relations with the labor-market
RCA dataset. Each occupation-skill pair is labelled according to whether it appears
only in ESCO, only in the market data, or in both sources. The final CSV keeps the
evidence from each source separate so later modules can use it appropriately.
"""
import pandas as pd

RCA_FILE = "full_rca_diagnostic.csv"
ESCO_FILE = "occupationSkillRelations_en.csv"

OUTPUT_FILE = "occupation_skill_profiles.csv"

def extract_uuid(uri: str) -> str:
    """Extract the UUID stored at the end of an ESCO URI."""
    if pd.isna(uri): return ""

    return str(uri).rstrip("/").split("/")[-1]


#This loads the labor-market RCA data that contains occupation-specific skill evidence.
market_df = pd.read_csv(RCA_FILE)

market_df = market_df[
    [
        "occupation_id",
        "occupation",
        "isco_group",
        "occupation_support",
        "skill_id",
        "skill",
        "x_os",
        "occupation_skill_total",
        "skill_total",
        "global_skill_total",
        "rca"
    ]
].copy()

#Loads the official ESCO occupation-skill relations.
esco_df = pd.read_csv(ESCO_FILE)
esco_df["occupation_id"] = (esco_df["occupationUri"].apply(extract_uuid))
esco_df["skill_id"] = (esco_df["skillUri"].apply(extract_uuid))

esco_df = esco_df[
    [
        "occupation_id",
        "occupationLabel",
        "skill_id",
        "skillLabel",
        "relationType",
        "skillType"
    ]
].copy()

esco_df = esco_df.rename(columns={
        "occupationLabel": "esco_occupation",
        "skillLabel": "esco_skill",
        "relationType": "esco_relation_type",
        "skillType": "esco_skill_type"
    }
)

#Restricts ESCO to the occupations included in the analytical market scope.
analytical_occupation_ids = set(market_df["occupation_id"].unique())

esco_df = esco_df[esco_df["occupation_id"].isin(analytical_occupation_ids)].copy()

profile_df = pd.merge(esco_df, market_df, on=["occupation_id", "skill_id"], how="outer", indicator=True)

#Labelling each data source.
source_mapping = {
    "left_only": "ESCO_ONLY",
    "right_only": "MARKET_ONLY",
    "both": "BOTH"
}

profile_df["source_type"] = (profile_df["_merge"].map(source_mapping))
profile_df = profile_df.drop(columns=["_merge"])
profile_df["occupation_name"] = (profile_df["occupation"].fillna(profile_df["esco_occupation"]))
profile_df["skill_name"] = (profile_df["skill"].fillna(profile_df["esco_skill"]))

#This marks whether this occupation-skill pair has observed market evidence.
profile_df["has_market_evidence"] = (profile_df["x_os"].notna())

#And this marks whether this occupation-skill pair is an official ESCO relation.
profile_df["has_esco_relation"] = (profile_df["esco_relation_type"].notna())

final_columns = [
    "occupation_id",
    "occupation_name",
    "isco_group",
    "occupation_support",

    "skill_id",
    "skill_name",

    "source_type",

    "has_esco_relation",
    "esco_relation_type",
    "esco_skill_type",

    "has_market_evidence",
    "x_os",
    "rca",

    "occupation_skill_total",
    "skill_total",
    "global_skill_total"
]

profile_df = profile_df[final_columns]

source_order = {
    "BOTH": 0,
    "ESCO_ONLY": 1,
    "MARKET_ONLY": 2
}

profile_df["source_order"] = (profile_df["source_type"].map(source_order))
profile_df = profile_df.sort_values(
    by=["occupation_name", "source_order", "esco_relation_type", "rca"],
    ascending=[True, True, True, False]
)

profile_df = profile_df.drop(columns=["source_order"])
profile_df.to_csv(OUTPUT_FILE, index=False, encoding="utf-8-sig")
