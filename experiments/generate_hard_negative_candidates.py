import numpy as np
import pandas as pd

EMBEDDINGS_FILE = ("data/processed/skill_embeddings_mpnet.npy")
INDEX_FILE = ("data/processed/skill_embeddings_index.csv")
OUTPUT_FILE = ("data/evaluation/semantic_hard_negative_candidates.csv")

MIN_SIMILARITY = 0.60
MAX_SIMILARITY = 0.80

TOP_K_PER_SKILL = 5
MAX_PAIRS = 100

def main():
    embeddings = np.load(EMBEDDINGS_FILE)

    index_df = pd.read_csv(INDEX_FILE)

    if len(index_df) != len(embeddings):
        raise ValueError("Index and embeddings have different sizes.")

    similarity_matrix = (embeddings @embeddings.T)

    candidate_pairs = []

    seen_pairs = set()

    for i in range(len(index_df)):
        similarities = (similarity_matrix[i])

        sorted_indices = np.argsort(similarities)[::-1]

        selected_for_skill = 0

        for j in sorted_indices:
            if i == j:
                continue
            similarity = float(similarities[j])

            if similarity < MIN_SIMILARITY:
                break
            if similarity > MAX_SIMILARITY:
                continue
            skill_a_id = (index_df.iloc[i]["skill_id"])
            skill_b_id = (index_df.iloc[j]["skill_id"])

            pair_key = tuple(sorted([skill_a_id, skill_b_id]))

            if pair_key in seen_pairs:
                continue
            seen_pairs.add(pair_key)

            skill_a_name = (index_df.iloc[i]["skill_name"])
            skill_b_name = (index_df.iloc[j]["skill_name"])

            candidate_pairs.append({
                "skill_a_id": skill_a_id,
                "skill_a": skill_a_name,
                "skill_b_id": skill_b_id,
                "skill_b": skill_b_name,
                "similarity":
                    round(similarity, 4),
                "candidate_type": "hard_candidate",
                "label": ""
            })

            selected_for_skill += 1

            if (selected_for_skill >= TOP_K_PER_SKILL):
                break

    candidates_df = pd.DataFrame(candidate_pairs)

    if candidates_df.empty:
        return

    candidates_df = (
        candidates_df
        .sort_values(
            by="similarity",
            ascending=False
        )
        .reset_index(
            drop=True
        )
    )

    candidates_df = (candidates_df.head(MAX_PAIRS))
    candidates_df.to_csv(OUTPUT_FILE, index=False)

if __name__ == "__main__":
    main()