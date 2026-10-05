import pandas as pd

CURRENT_PAIRS_FILE = ("data/evaluation/semantic_skill_pairs.csv")

BALANCED_HARD_FILE = ("data/evaluation/semantic_balanced_hard_candidates_labeled.csv")

OUTPUT_FILE = ("data/evaluation/semantic_skill_pairs_balanced.csv")

def make_pair_key(row):
    """
    Treat A-B and B-A as the same pair.
    """
    return tuple(sorted([str(row["skill_a_id"]), str(row["skill_b_id"])]))

def main():

    print("=" * 80)
    print("BUILD BALANCED SEMANTIC VALIDATION DATASET")
    print("=" * 80)

    #1. Load current 203-pair dataset
    current_df = pd.read_csv(CURRENT_PAIRS_FILE)

    print("Current semantic pairs:", len(current_df))

    #2. Recover the original 110 pairs
    #Remove MPNet-derived hard candidates.
    base_df = current_df[current_df["candidate_type"] != "hard_candidate"].copy()

    print("Original base pairs recovered:", len(base_df))

    #3. Load labelled balanced hard candidates
    balanced_df = pd.read_csv(BALANCED_HARD_FILE)

    print("Balanced hard candidates:", len(balanced_df))

    #4. Convert balanced candidates to same schema as semantic_skill_pairs.csv
    balanced_aligned = pd.DataFrame({
        "skill_a_id": balanced_df["skill_a_id"],
        "skill_a": balanced_df["skill_a"],
        "skill_b_id": balanced_df["skill_b_id"],
        "skill_b": balanced_df["skill_b"],
        "candidate_type": "balanced_hard",
        "occupation": "",
        "lexical_score": "",
        "label": balanced_df["label"].astype(int)
    })

    #5. Safety check for duplicates
    base_keys = set(base_df.apply( make_pair_key, axis=1))

    duplicate_mask = (
        balanced_aligned.apply(
            make_pair_key,
            axis=1
        ).isin(base_keys)
    )

    duplicate_count = int(duplicate_mask.sum())

    print("Duplicates against original base:", duplicate_count)

    if duplicate_count > 0:
        print("Removing duplicate balanced pairs...")

        balanced_aligned = (balanced_aligned[~duplicate_mask].copy())

    #6. Combine
    final_df = pd.concat(
        [
            base_df,
            balanced_aligned
        ],
        ignore_index=True
    )

    #7. Final validation
    positive_count = int((final_df["label"] == 1).sum())

    negative_count = int((final_df["label"] == 0).sum())

    print("\nFinal pairs:", len(final_df))

    print("Positive pairs:", positive_count)

    print("Negative pairs:", negative_count)

    print("Positive ratio:", f"{positive_count / len(final_df):.2%}")



    final_df.to_csv(OUTPUT_FILE, index=False)
    print("\nSaved to:" )
    print(OUTPUT_FILE)

if __name__ == "__main__":
    main()