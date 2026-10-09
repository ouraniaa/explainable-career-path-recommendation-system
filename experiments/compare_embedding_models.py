import numpy as np
import pandas as pd

from sentence_transformers import SentenceTransformer
from sklearn.metrics import (precision_score, recall_score, f1_score, accuracy_score, confusion_matrix)
from sklearn.model_selection import StratifiedKFold

CURRENT_PAIRS_FILE = "data/evaluation/semantic_skill_pairs.csv"

STRESS_TEST_FILE = ("data/evaluation/semantic_balanced_hard_candidates_labeled.csv")
ESCO_SKILLS_FILE = "data/raw/skills_en.csv"
OUTPUT_FILE = ("data/evaluation/semantic_model_evaluation_results.csv")

MODELS = {
    "MiniLM": "sentence-transformers/all-MiniLM-L6-v2",
    "MPNet": "sentence-transformers/all-mpnet-base-v2",
    "BGE-small": "BAAI/bge-small-en-v1.5"
}

REPRESENTATIONS = ["name", "name_description", "name_alt_description"]

N_SPLITS = 5
RANDOM_STATE = 42

def extract_esco_id(concept_uri):
    """
    Extracts the ESCO skill identifier from a concept URI.
    """
    if pd.isna(concept_uri):
        return None

    return (
        str(concept_uri)
        .strip()
        .rstrip("/")
        .split("/")[-1]
    )


def load_esco_skills():
    """
    Loads official ESCO skill metadata and creates a lookup
    indexed by ESCO skill identifier.
    """
    df = pd.read_csv(ESCO_SKILLS_FILE, low_memory=False)

    required_columns = [
        "conceptUri",
        "preferredLabel",
        "altLabels",
        "description"
    ]

    for column in required_columns:
        if column not in df.columns:
            raise ValueError(f"Missing ESCO column: {column}")

    df["skill_id"] = df["conceptUri"].apply(extract_esco_id)

    lookup = {}

    for _, row in df.iterrows():
        skill_id = row["skill_id"]

        if not skill_id:
            continue

        preferred_label = (
            ""
            if pd.isna(row["preferredLabel"])
            else str(row["preferredLabel"]).strip()
        )

        alt_labels = (
            ""
            if pd.isna(row["altLabels"])
            else str(row["altLabels"]).strip()
        )

        description = (
            ""
            if pd.isna(row["description"])
            else str(row["description"]).strip()
        )

        lookup[skill_id] = {
            "preferred_label": preferred_label,
            "alt_labels": alt_labels,
            "description": description
        }

    return lookup


def build_skill_text(skill_id, fallback_name, skill_lookup, representation):
    """
    Builds one of the evaluated skill text representations:
    name, name with description, or name with alternative
    labels and description.
    """
    skill_data = skill_lookup.get(str(skill_id))
    fallback_name = str(fallback_name).strip()

    if skill_data is None:
        return fallback_name

    name = (
        skill_data["preferred_label"]
        or fallback_name
    )

    alt_labels = skill_data["alt_labels"]
    description = skill_data["description"]

    if representation == "name":
        return name

    if representation == "name_description":
        if description:
            return f"{name}: {description}"

        return name

    if representation == "name_alt_description":
        parts = [name]

        if alt_labels:
            parts.append(f"Alternative labels: {alt_labels}")

        if description:
            parts.append(f"Description: {description}")

        return " | ".join(parts)

    raise ValueError(f"Unknown representation: {representation}")


def load_base_dataset():
    """
    Recovers the original labelled validation pairs by
    excluding the old MPNet-derived hard candidates.
    """
    df = pd.read_csv(CURRENT_PAIRS_FILE)

    if "candidate_type" not in df.columns:
        raise ValueError("candidate_type column missing from semantic_skill_pairs.csv")

    base_df = df[
        df["candidate_type"] != "hard_candidate"
    ].copy()

    return base_df.reset_index(drop=True)


def load_stress_dataset():
    """
    Loads the independently labelled balanced hard
    stress-test dataset.
    """
    df = pd.read_csv(STRESS_TEST_FILE)

    return df.reset_index(drop=True)


def build_pair_texts(df, skill_lookup, representation):
    """
    Converts every skill pair into the selected
    text representation.
    """
    text_a_list = []
    text_b_list = []

    for _, row in df.iterrows():
        text_a = build_skill_text(
            skill_id=row["skill_a_id"],
            fallback_name=row["skill_a"],
            skill_lookup=skill_lookup,
            representation=representation
        )

        text_b = build_skill_text(
            skill_id=row["skill_b_id"],
            fallback_name=row["skill_b"],
            skill_lookup=skill_lookup,
            representation=representation
        )

        text_a_list.append(text_a)
        text_b_list.append(text_b)

    return text_a_list, text_b_list


def calculate_similarities(model, text_a_list, text_b_list):
    """
    Generates normalized embeddings and calculates
    cosine similarity through their dot product.
    """
    embeddings_a = model.encode(text_a_list, normalize_embeddings=True, show_progress_bar=False)

    embeddings_b = model.encode(text_b_list, normalize_embeddings=True, show_progress_bar=False)

    similarities = (embeddings_a * embeddings_b).sum(axis=1)

    return similarities


def evaluate_threshold(labels, similarities, threshold):
    """
    Evaluates one fixed similarity threshold.
    """
    predictions = (similarities >= threshold).astype(int)

    precision = precision_score(labels, predictions, zero_division=0)

    recall = recall_score(labels, predictions, zero_division=0)

    f1 = f1_score(labels, predictions, zero_division=0)

    accuracy = accuracy_score(labels, predictions)

    tn, fp, fn, tp = confusion_matrix(labels, predictions, labels=[0, 1]).ravel()

    return {
        "threshold": threshold,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "accuracy": accuracy,
        "true_negatives": int(tn),
        "false_positives": int(fp),
        "false_negatives": int(fn),
        "true_positives": int(tp)
    }


def find_best_threshold(labels, similarities):
    """
    Searches thresholds from 0.20 to 0.95.

    Primary criterion:
    highest F1.

    Tie-break:
    highest precision.
    """
    thresholds = np.arange(0.20, 0.96, 0.01)

    results = []

    for threshold in thresholds:
        result = evaluate_threshold(labels, similarities, threshold)

        results.append(result)

    best_result = max(
        results,
        key=lambda x: (
            x["f1"],
            x["precision"]
        )
    )

    return best_result


def cross_validate(labels, similarities):
    """
    Performs stratified 5-fold cross-validation.
    """
    skf = StratifiedKFold(n_splits=N_SPLITS, shuffle=True, random_state=RANDOM_STATE)

    fold_results = []

    for fold_number, (train_indices, test_indices) in enumerate(
        skf.split(similarities, labels),
        start=1
    ):
        train_labels = labels[train_indices]
        train_similarities = similarities[train_indices]
        test_labels = labels[test_indices]
        test_similarities = similarities[test_indices]

        best_train = find_best_threshold(train_labels, train_similarities)

        threshold = best_train["threshold"]

        test_result = evaluate_threshold(test_labels, test_similarities, threshold)

        fold_results.append({
            "fold": fold_number,
            **test_result
        })

    return fold_results


def summarize_cv(fold_results):
    thresholds = np.array([
        result["threshold"]
        for result in fold_results
    ])

    precisions = np.array([
        result["precision"]
        for result in fold_results
    ])

    recalls = np.array([
        result["recall"]
        for result in fold_results
    ])

    f1_scores = np.array([
        result["f1"]
        for result in fold_results
    ])

    accuracies = np.array([
        result["accuracy"]
        for result in fold_results
    ])

    return {
        "cv_mean_threshold": thresholds.mean(),
        "cv_std_threshold": thresholds.std(),
        "cv_mean_precision": precisions.mean(),
        "cv_std_precision": precisions.std(),
        "cv_mean_recall": recalls.mean(),
        "cv_std_recall": recalls.std(),
        "cv_mean_f1": f1_scores.mean(),
        "cv_std_f1": f1_scores.std(),
        "cv_mean_accuracy": accuracies.mean(),
        "cv_std_accuracy": accuracies.std()
    }


def main():
    base_df = load_base_dataset()
    stress_df = load_stress_dataset()

    base_labels = (
        base_df["label"]
        .astype(int)
        .values
    )

    stress_labels = (
        stress_df["label"]
        .astype(int)
        .values
    )

    skill_lookup = load_esco_skills()

    final_results = []

    for representation in REPRESENTATIONS:
        base_text_a, base_text_b = build_pair_texts(base_df, skill_lookup, representation)

        stress_text_a, stress_text_b = build_pair_texts(stress_df, skill_lookup, representation)

        for model_name, model_path in MODELS.items():
            model = SentenceTransformer(model_path)

            #Phase 1: Evaluate threshold selection through stratified 5-fold cross-validation.
            base_similarities = calculate_similarities(model, base_text_a, base_text_b)

            fold_results = cross_validate(base_labels, base_similarities)

            cv_summary = summarize_cv(fold_results)

            calibration_result = find_best_threshold(base_labels, base_similarities)

            deployment_threshold = (calibration_result["threshold"])

            #Phase 2: Apply the fixed deployment threshold to the independent balanced hard stress-test set.
            stress_similarities = calculate_similarities(model, stress_text_a, stress_text_b)

            stress_result = evaluate_threshold(stress_labels, stress_similarities, deployment_threshold)

            final_results.append({
                "representation": representation,
                "model": model_name,
                "deployment_threshold": deployment_threshold,
                **cv_summary,
                "stress_precision": stress_result["precision"],
                "stress_recall": stress_result["recall"],
                "stress_f1": stress_result["f1"],
                "stress_accuracy": stress_result["accuracy"],
                "stress_true_negatives": stress_result["true_negatives"],
                "stress_false_positives": stress_result["false_positives"],
                "stress_false_negatives": stress_result["false_negatives"],
                "stress_true_positives": stress_result["true_positives"]
            })

    results_df = pd.DataFrame(final_results)

    results_df = (
        results_df
        .sort_values(
            by="cv_mean_f1",
            ascending=False
        )
        .reset_index(drop=True)
    )

    results_df.to_csv(OUTPUT_FILE, index=False)

if __name__ == "__main__":
    main()