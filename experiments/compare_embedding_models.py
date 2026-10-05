import numpy as np
import pandas as pd

from sentence_transformers import SentenceTransformer
from sklearn.metrics import (precision_score, recall_score, f1_score, accuracy_score, confusion_matrix)
from sklearn.model_selection import StratifiedKFold

#This file currently contains: original 110 pairs and the old MPNet-derived hard candidates
#We recover the original 110 automatically by excluding:candidate_type == "hard_candidate"
CURRENT_PAIRS_FILE = ("data/evaluation/semantic_skill_pairs.csv")

#Independent balanced hard stress-test set
STRESS_TEST_FILE = ("data/evaluation/semantic_balanced_hard_candidates_labeled.csv")

ESCO_SKILLS_FILE = ("data/raw/skills_en.csv")


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


REPRESENTATIONS = ["name", "name_description", "name_alt_description"]

N_SPLITS = 5
RANDOM_STATE = 42


# NORMALIZE ESCO ID
def extract_esco_id(concept_uri):
    """
    Converts:
        http://data.europa.eu/esco/skill/<UUID>
    into:
        <UUID>
    """

    if pd.isna(concept_uri):
        return None

    return (
        str(concept_uri)
        .strip()
        .rstrip("/")
        .split("/")[-1]
    )

# LOAD ESCO SKILLS
def load_esco_skills():
    """
    Loads official ESCO metadata.
    Creates:
        skill_id -> {
            preferred_label,
            alt_labels,
            description
        }
    """

    print("\nLoading ESCO skills...")

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

        alt_labels = (
            ""
            if pd.isna(row["altLabels"])
            else str(
                row["altLabels"]
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
            "alt_labels": alt_labels,
            "description": description
        }

    print("ESCO skills loaded:", len(lookup))
    return lookup


#BUILD TEXT REPRESENTATION
def build_skill_text(
    skill_id,
    fallback_name,
    skill_lookup,
    representation
):
    """
    Builds one of three representations:
    1. name
    2. name_description
    3. name_alt_description
    """

    skill_data = (skill_lookup.get(str(skill_id)))

    fallback_name = str(fallback_name).strip()

    if skill_data is None:
        return fallback_name

    name = (skill_data["preferred_label"] or fallback_name)
    alt_labels = (skill_data["alt_labels" ])
    description = (skill_data["description"])

    #NAME ONLY
    if representation == "name":
        return name

    #NAME + DESCRIPTION
    if (representation == "name_description"):
        if description:
            return (
                f"{name}: "
                f"{description}"
            )
        return name

    #NAME + ALT LABELS + DESCRIPTION
    if (representation == "name_alt_description"):
        parts = [name]
        if alt_labels:
            parts.append(
                f"Alternative labels: "
                f"{alt_labels}"
            )

        if description:
            parts.append(
                f"Description: "
                f"{description}"
            )
        return " | ".join(parts)

    raise ValueError(
        f"Unknown representation: "
        f"{representation}"
    )


#LOAD ORIGINAL 110 PAIRS
def load_base_dataset():
    """
    Recovers the original 110 labelled pairs.
    Old MPNet-specific hard candidates are excluded.
    """

    df = pd.read_csv(CURRENT_PAIRS_FILE)

    if ("candidate_type" not in df.columns):
        raise ValueError("candidate_type column missing from semantic_skill_pairs.csv")

    base_df = df[df["candidate_type"] != "hard_candidate"].copy()
    base_df = (base_df.reset_index(drop=True))
    return base_df


#LOAD BALANCED HARD STRESS TEST
def load_stress_dataset():
    df = pd.read_csv(STRESS_TEST_FILE)
    df = (df.reset_index(drop=True))
    return df

#BUILD PAIR TEXTS
def build_pair_texts(df, skill_lookup, representation):
    """
    Converts every skill pair into the selected text representation.
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
    return (text_a_list, text_b_list)


#CALCULATE SIMILARITIES
def calculate_similarities(model, text_a_list, text_b_list):
    """
    Generates normalized embeddings.
    Because embeddings are normalized: dot product == cosine similarity
    """

    embeddings_a = model.encode(text_a_list, normalize_embeddings=True, show_progress_bar=False)
    embeddings_b = model.encode(text_b_list, normalize_embeddings=True, show_progress_bar=False)

    similarities = (embeddings_a * embeddings_b).sum(axis=1)
    return similarities

#THRESHOLD EVALUATION
def evaluate_threshold(labels, similarities, threshold):
    """
    Applies one fixed threshold.
    """

    predictions = (similarities >= threshold).astype(int)
    precision = precision_score(labels, predictions, zero_division=0)
    recall = recall_score(labels, predictions, zero_division=0)
    f1 = f1_score(labels, predictions, zero_division=0)
    accuracy = accuracy_score(labels, predictions)

    tn, fp, fn, tp = (confusion_matrix(labels, predictions, labels=[0, 1]).ravel())

    return {
        "threshold": threshold,
        "precision": precision, 
        "recall": recall,
        "f1":f1, 
        "accuracy": accuracy,
        "true_negatives": int(tn), 
        "false_positives": int(fp),
        "false_negatives": int(fn),
        "true_positives": int(tp)
    }


#FIND BEST THRESHOLD
def find_best_threshold(labels, similarities):
    """
    Searches thresholds from 0.20 to 0.95.
    Primary criterion: highest F1
    Tie-break: highest precision
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


#CROSS-VALIDATION
def cross_validate(labels, similarities):
    """
    Stratified 5-fold CV.
    In every fold:
    TRAIN: select threshold
    TEST: evaluate selected threshold
    """

    skf = StratifiedKFold(
        n_splits=N_SPLITS,
        shuffle=True,
        random_state=RANDOM_STATE
    )

    fold_results = []

    for fold_number, (train_indices, test_indices) in enumerate(skf.split(similarities, labels),start=1):
        train_labels = (labels[train_indices])
        train_similarities = (similarities[train_indices])

        test_labels = (labels[test_indices])
        test_similarities = (similarities[test_indices])

        #Threshold selected ONLY on training data
        best_train = (find_best_threshold(train_labels, train_similarities))

        threshold = (best_train["threshold"])

        #Test on unseen fold
        test_result = (evaluate_threshold(test_labels, test_similarities, threshold))

        fold_results.append({
            "fold": fold_number,
            **test_result
        })

    return fold_results

#SUMMARIZE CV
def summarize_cv(fold_results):
    thresholds = np.array([
        result["threshold"]
        for result
        in fold_results
    ])

    precisions = np.array([
        result["precision"]
        for result
        in fold_results
    ])

    recalls = np.array([
        result["recall"]
        for result
        in fold_results
    ])

    f1_scores = np.array([
        result["f1"]
        for result
        in fold_results
    ])

    accuracies = np.array([
        result["accuracy"]
        for result
        in fold_results
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


#DATASET INFO
def print_dataset_info(name, df):
    positive_count = int((df["label"] == 1).sum())
    negative_count = int((df["label"] == 0).sum())

    print(f"\n{name}")
    print("Total pairs:", len(df))
    print("Positive pairs:", positive_count)
    print("Negative pairs:", negative_count)


def main():
    print("=" * 100)
    print("SEMANTIC MODEL EVALUATION")
    print("PHASE 1: 5-FOLD CV")
    print("PHASE 2: FIXED-THRESHOLD HARD STRESS TEST")
    print("=" * 100)

    #Load datasets
    base_df = (load_base_dataset())
    stress_df = (load_stress_dataset())

    print_dataset_info("BASE VALIDATION DATASET", base_df)
    print_dataset_info("BALANCED HARD STRESS TEST", stress_df)

    base_labels = (base_df["label"].astype(int).values)

    stress_labels = (stress_df["label"].astype(int).values)

    #ESCO metadata
    skill_lookup = (load_esco_skills())
    final_results = []

    #REPRESENTATION LOOP
    for representation in (REPRESENTATIONS):
        print("\n" + "#" * 100)
        print("REPRESENTATION:", representation)
        print("#" * 100)

        #Build representation for base dataset
        (base_text_a, base_text_b) = build_pair_texts(base_df, skill_lookup, representation)

        #Build representation for stress dataset
        (stress_text_a, stress_text_b) = build_pair_texts(stress_df, skill_lookup, representation)

        #MODEL LOOP
        for (model_name, model_path) in MODELS.items():
            print("\n" + "=" * 100)

            print(
                f"{model_name} "
                f"+ {representation}"
            )
            print("=" * 100)

            model = SentenceTransformer(model_path)

            #PHASE 1
            print("\nPHASE 1 - 5-FOLD CROSS-VALIDATION")

            base_similarities = (calculate_similarities(model, base_text_a, base_text_b))

            fold_results = (cross_validate(base_labels, base_similarities))

            for result in fold_results:
                print(
                    f"Fold "
                    f"{result['fold']}: "
                    f"threshold="
                    f"{result['threshold']:.2f} | "
                    f"precision="
                    f"{result['precision']:.4f} | "
                    f"recall="
                    f"{result['recall']:.4f} | "
                    f"F1="
                    f"{result['f1']:.4f} | "
                    f"accuracy="
                    f"{result['accuracy']:.4f}"
                )

            cv_summary = (summarize_cv(fold_results))

            print("\nCV summary:")
            print(
                f"Mean threshold: "
                f"{cv_summary['cv_mean_threshold']:.4f} "
                f"+/- "
                f"{cv_summary['cv_std_threshold']:.4f}"
            )
            print(
                f"Mean precision: "
                f"{cv_summary['cv_mean_precision']:.4f}"
            )
            print(
                f"Mean recall: "
                f"{cv_summary['cv_mean_recall']:.4f}"
            )
            print(
                f"Mean F1: "
                f"{cv_summary['cv_mean_f1']:.4f} "
                f"+/- "
                f"{cv_summary['cv_std_f1']:.4f}"
            )
            print(
                f"Mean accuracy: "
                f"{cv_summary['cv_mean_accuracy']:.4f}"
            )

            #FINAL THRESHOLD CALIBRATION      
            #After unbiased CV evaluation, calibrate one deployment threshold using ALL 110 base pairs.
            #This threshold will be frozen before the stress test.

            calibration_result = (find_best_threshold(base_labels, base_similarities))

            deployment_threshold = (calibration_result["threshold"])

            print("\nDeployment threshold calibrated on all base pairs:")
            print(f"{deployment_threshold:.2f}")

            #PHASE 2
            print("\nPHASE 2 - BALANCED HARD STRESS TEST")
            print("Threshold is FIXED. No tuning on stress-test data.")

            stress_similarities = (calculate_similarities(model, stress_text_a, stress_text_b))
            stress_result = (evaluate_threshold(stress_labels, stress_similarities, deployment_threshold))

            print(
                f"Threshold: "
                f"{deployment_threshold:.2f}"
            )
            print(
                f"Precision: "
                f"{stress_result['precision']:.4f}"
            )
            print(
                f"Recall: "
                f"{stress_result['recall']:.4f}"
            )
            print(
                f"F1: "
                f"{stress_result['f1']:.4f}"
            )
            print(
                f"Accuracy: "
                f"{stress_result['accuracy']:.4f}"
            )
            print("\nConfusion matrix:")
            print("True negatives:", stress_result["true_negatives"])
            print("False positives:", stress_result["false_positives"])
            print("False negatives:", stress_result["false_negatives"])
            print("True positives:", stress_result["true_positives"])

            #Store result
            final_results.append({
                "representation": representation, 
                "model": model_name,
                "deployment_threshold": deployment_threshold **cv_summary,
                "stress_precision": stress_result["precision"],
                "stress_recall": stress_result["recall"],
                "stress_f1": stress_result["f1"],
                "stress_accuracy": stress_result["accuracy"], 
                "stress_false_positives": stress_result["false_positives"],
                "stress_false_negatives": stress_result["false_negatives"]
            })

    #FINAL COMPARISON
    results_df = pd.DataFrame(final_results)

    # Primary ranking: unbiased CV F1 on base dataset
    results_df = (results_df.sort_values(by="cv_mean_f1", ascending=False))

    print("\n" + "=" * 140)
    print("FINAL MODEL COMPARISON")
    print("=" * 140)

    columns = [
        "representation",
        "model",
        "deployment_threshold",
        "cv_mean_threshold",
        "cv_std_threshold",
        "cv_mean_precision",
        "cv_mean_recall",
        "cv_mean_f1",
        "cv_std_f1",
        "cv_mean_accuracy",
        "stress_precision",
        "stress_recall",
        "stress_f1",
        "stress_accuracy",
        "stress_false_positives",
        "stress_false_negatives"
    ]

    print(
        results_df[
            columns
        ].to_string(
            index=False,
            float_format=lambda x:
                f"{x:.4f}"
        )
    )

    print("\nRanking is based on cv_mean_f1 from the original base validation dataset.")
    print("Stress-test metrics are reported separately and are NOT used to tune the threshold.")

if __name__ == "__main__":
    main()