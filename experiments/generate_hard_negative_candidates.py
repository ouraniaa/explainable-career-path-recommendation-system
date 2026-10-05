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

    print("=" * 80)
    print("GENERATE HARD NEGATIVE CANDIDATES")
    print("=" * 80)

    #Load embeddings + skill index
    embeddings = np.load(EMBEDDINGS_FILE)

    index_df = pd.read_csv(INDEX_FILE)

    print("Skills loaded:", len(index_df))
    print("Embedding matrix shape:", embeddings.shape)

    if len(index_df) != len(embeddings):
        raise ValueError("Index and embeddings have different sizes.")

    #Cosine similarity matrix
    #Embeddings are already normalized, therefore: cosine_similarity = dot product
    similarity_matrix = (embeddings @embeddings.T)

    candidate_pairs = []

    seen_pairs = set()

    #For every skill, find similar skills
    for i in range(len(index_df)):
        similarities = (similarity_matrix[i])

        #Highest similarities first
        sorted_indices = np.argsort(similarities)[::-1]

        selected_for_skill = 0

        for j in sorted_indices:
            #Ignore itself
            if i == j:
                continue
            similarity = float(similarities[j])

            #Because values are sorted descending, once we go below MIN we can stop.
            if similarity < MIN_SIMILARITY:
                break
            if similarity > MAX_SIMILARITY:
                continue
            skill_a_id = (index_df.iloc[i]["skill_id"])
            skill_b_id = (index_df.iloc[j]["skill_id"])

            #Canonical ordering prevents duplicated A-B / B-A pairs.
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

    #Convert to DataFrame
    candidates_df = pd.DataFrame(candidate_pairs)

    if candidates_df.empty:
        print("\nNo candidate pairs found.")
        return

    #Highest similarity first
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

    #Limit number of candidates
    candidates_df = (
        candidates_df
        .head(
            MAX_PAIRS
        )
    )

    candidates_df.to_csv(OUTPUT_FILE, index=False)

    print("\nCandidate pairs generated:", len(candidates_df))
    print("\nSimilarity range:")
    print("Min:", candidates_df["similarity"].min())
    print("Max:", candidates_df["similarity"].max())
    print("\nSaved to:")
    print(OUTPUT_FILE)

    #Preview top candidates
    print("\n" + "=" * 80)
    print("TOP CANDIDATES")
    print("=" * 80)
    for _, row in (candidates_df.head(20).iterrows()):
        print(f"{row['skill_a']}")
        print(
            f"    <-> "
            f"{row['skill_b']}"
        )
        print(
            f"    similarity = "
            f"{row['similarity']}"
        )
        print("-" * 80)

if __name__ == "__main__":
    main()