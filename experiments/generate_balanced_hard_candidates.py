import numpy as np
import pandas as pd

from sentence_transformers import SentenceTransformer

PAIRS_FILE = ("data/evaluation/semantic_skill_pairs.csv")

ESCO_SKILLS_FILE = ("data/raw/skills_en.csv")

SKILL_INDEX_FILE = ("data/processed/skill_embeddings_index.csv")

OUTPUT_FILE = ("data/evaluation/semantic_balanced_hard_candidates.csv")

MODELS = {
    "MiniLM":
        "sentence-transformers/"
        "all-MiniLM-L6-v2",

    "MPNet":
        "sentence-transformers/"
        "all-mpnet-base-v2",

    "BGE-small":
        "BAAI/"
        "bge-small-en-v1.5",
}

#Equal quota for every model
CANDIDATES_PER_MODEL = 30

#Prevent one very generic skill from dominating
MAX_PAIRS_PER_SKILL_PER_MODEL = 2


#NORMALIZE ESCO ID
def extract_esco_id(concept_uri):
    if pd.isna(concept_uri):
        return None
    return (
        str(concept_uri)
        .strip()
        .rstrip("/")
        .split("/")[-1]
    )


#LOAD ESCO METADATA
def load_esco_lookup():
    df = pd.read_csv(ESCO_SKILLS_FILE, low_memory=False)

    df["skill_id"] = (df["conceptUri"].apply(extract_esco_id))

    lookup = {}

    for _, row in df.iterrows():
        skill_id = row["skill_id"]
        if not skill_id:
            continue
        preferred_label = (
            ""
            if pd.isna(row["preferredLabel"])
            else str(
                row["preferredLabel"]
            ).strip()
        )

        description = (
            ""
            if pd.isna(row["description"])
            else str(
                row["description"]
            ).strip()
        )

        lookup[skill_id] = {
            "preferred_label": preferred_label,
            "description": description
        }

    return lookup


#BUILD NAME + DESCRIPTION REPRESENTATION
def build_skill_text(skill_id, fallback_name, esco_lookup):
    data = esco_lookup.get(skill_id)
    if data is None:
        return str(fallback_name).strip()

    name = (data["preferred_label"] or str(fallback_name).strip())

    description = (data["description"])

    if description:
        return (
            f"{name}: "
            f"{description}"
        )

    return name


#PAIR KEY
def make_pair_key(skill_a_id, skill_b_id):
    """
    A-B and B-A are treated as the same pair.
    """

    return tuple(
        sorted([
            str(skill_a_id),
            str(skill_b_id)
        ])
    )


#LOAD ORIGINAL BASE DATASET
def load_original_base_pairs():
    """
    Current semantic_skill_pairs.csv contains:
    - original 110 pairs
    - MPNet-derived hard candidates

    We recover the original dataset by removing rows 
    whose candidate_type == hard_candidate.
    """

    df = pd.read_csv(PAIRS_FILE)

    base_df = df[df["candidate_type"] != "hard_candidate"].copy()

    print("Current dataset pairs:", len(df))
    print("Original base pairs recovered:", len(base_df))

    return base_df


#LOAD 699 CANONICAL SKILLS
def load_canonical_skills(esco_lookup):
    index_df = pd.read_csv(SKILL_INDEX_FILE)

    skills = []

    for _, row in (index_df.iterrows()):
        skill_id = str(row["skill_id"])

        fallback_name = str(row["skill_name"])

        text = build_skill_text(skill_id, fallback_name, esco_lookup)

        esco_data = (esco_lookup.get(skill_id, {}))

        skill_name = (esco_data.get("preferred_label") or fallback_name)

        skills.append({
            "skill_id": skill_id,
            "skill_name": skill_name,
            "text": text
        })

    return skills


#FIND TOP HARD CANDIDATES FOR ONE MODEL

def select_candidates_for_model(
    model_name,
    model_path,
    skills,
    existing_pair_keys
):

    print("\n" + "=" * 80)
    print("Generating candidates for:", model_name)
    print("=" * 80)

    model = SentenceTransformer(model_path)

    texts = [skill["text"] for skill in skills]

    embeddings = model.encode(texts, normalize_embeddings=True, show_progress_bar=True)

    #Normalized vectors: dot product == cosine similarity
    similarity_matrix = (embeddings @ embeddings.T)

    raw_candidates = []

    skill_count = len(skills)

    # Only upper triangle: avoids duplicate A-B / B-A
    for i in range(skill_count):
        for j in range(i + 1, skill_count):
            pair_key = (make_pair_key(skills[i]["skill_id"], skills[j]["skill_id"]))

            #Do not select pairs already present in the original 110.
            if (pair_key in existing_pair_keys):
                continue

            similarity = float(similarity_matrix[i, j])

            raw_candidates.append({
                "skill_a_id": skills[i]["skill_id"],
                "skill_a": skills[i]["skill_name"],
                "skill_b_id": skills[j]["skill_id"],
                "skill_b": skills[j]["skill_name"],
                "similarity": similarity,
                "pair_key": pair_key
            })

    #Highest similarity first
    raw_candidates.sort(
        key=lambda x:
            x["similarity"],
        reverse=True
    )

    selected = []

    skill_usage = {}

    for candidate in raw_candidates:
        skill_a_id = (candidate["skill_a_id"])
        skill_b_id = (candidate["skill_b_id"])

        count_a = skill_usage.get(skill_a_id, 0)
        count_b = skill_usage.get(skill_b_id, 0)

        #Diversity constraint: don't let one skill dominate
        if (count_a >= MAX_PAIRS_PER_SKILL_PER_MODEL):
            continue
        if (count_b >= MAX_PAIRS_PER_SKILL_PER_MODEL):
            continue

        selected.append(candidate)

        skill_usage[skill_a_id] = count_a + 1
        skill_usage[skill_b_id] = count_b + 1

        if (len(selected) >= CANDIDATES_PER_MODEL):
            break

    print("Selected candidates:", len(selected))

    return (selected, similarity_matrix)

def main():

    print("=" * 80)
    print("MODEL-BALANCED HARD CANDIDATE GENERATION")
    print("=" * 80)

    #Load original 110 validation pairs
    base_df = (load_original_base_pairs())
    base_pair_keys = set()

    for _, row in (base_df.iterrows()):
        base_pair_keys.add(
            make_pair_key(
                row["skill_a_id"],
                row["skill_b_id"]
            )
        )

    #Load ESCO metadata
    esco_lookup = (load_esco_lookup())

    print("ESCO skills loaded:", len(esco_lookup))

    #Load analytical canonical skills
    skills = (load_canonical_skills(esco_lookup))

    print("Canonical skills:", len(skills))

    #Map ID -> matrix position
    skill_position = {
        skill["skill_id"]:
            index

        for index, skill in enumerate(skills)
    }

    #Generate equal candidate quota from every model
    selections = {}

    similarity_matrices = {}

    for (model_name, model_path) in MODELS.items():
        selected, matrix = (
            select_candidates_for_model(
                model_name,
                model_path,
                skills,
                base_pair_keys
            )
        )

        selections[model_name] = selected
        similarity_matrices[model_name] = matrix

    #Union + deduplication
    union_candidates = {}

    for (model_name, selected_candidates) in selections.items():
        for candidate in (selected_candidates):
            key = candidate["pair_key"]
            if (key not in union_candidates):
                union_candidates[key] = {
                    "skill_a_id": candidate["skill_a_id"],
                    "skill_a": candidate["skill_a"],
                    "skill_b_id": candidate["skill_b_id"],
                    "skill_b": candidate["skill_b"],
                    "selected_by": []
                }

            union_candidates[key]["selected_by"].append(model_name)

    #Add all three models' similarity scores
    output_rows = []

    for (pair_key,candidate) in union_candidates.items():
        skill_a_id = (candidate["skill_a_id"])
        skill_b_id = (candidate["skill_b_id"])

        i = skill_position[skill_a_id]
        j = skill_position[skill_b_id]

        row = {
            "skill_a_id": skill_a_id, 
            "skill_a": candidate["skill_a"],
            "skill_b_id": skill_b_id,
            "skill_b": candidate["skill_b"],
            "selected_by":
                "|".join(candidate["selected_by"]),
            "minilm_similarity": 
                round(
                    float(similarity_matrices["MiniLM"][i, j]), 4),
            "mpnet_similarity":
                round(
                    float(similarity_matrices["MPNet"][i, j]), 4),
            "bge_similarity":
                round(
                    float(similarity_matrices["BGE-small"][i, j]), 4),
            "candidate_type": "balanced_hard",
            "label": ""
        }

        output_rows.append(row)

    output_df = pd.DataFrame(output_rows)

    #Pairs selected by more than one model first.
    output_df["selected_by_count"] = (output_df["selected_by"].apply(
            lambda x:
                len(
                    x.split("|")
                )
        )
    )

    output_df = (
        output_df
        .sort_values(
            by=[
                "selected_by_count",
                "selected_by"
            ],
            ascending=[
                False,
                True
            ]
        )
        .drop(
            columns=[
                "selected_by_count"
            ]
        )
        .reset_index(
            drop=True
        )
    )

    output_df.to_csv(OUTPUT_FILE, index=False)

    print("\n" + "=" * 80)
    print("BALANCED HARD SET SUMMARY")
    print("=" * 80)
    print(
        "MiniLM selections:", len(selections["MiniLM"])
    )
    print(
        "MPNet selections:", len(selections["MPNet"])
    )
    print(
        "BGE-small selections:", len(selections["BGE-small"])
    )
    print(
        "Total selections before dedup:", sum(len(x)
            for x
            in selections.values()
        )
    )
    print("Unique candidates after dedup:", len(output_df))
    print("\nSaved to:")
    print(OUTPUT_FILE)
    print("\nSelected-by distribution:")
    print(
        output_df[
            "selected_by"
        ]
        .value_counts()
        .to_string()
    )

if __name__ == "__main__":
    main()