import random
import re
import os
import pandas as pd

from difflib import SequenceMatcher
from dotenv import load_dotenv
from neo4j import GraphDatabase

load_dotenv()

URI = os.getenv("NEO4J_URI")
USER = os.getenv("NEO4J_USER")
PASSWORD = os.getenv("NEO4J_PASSWORD")

if not URI or not USER or not PASSWORD:
    raise RuntimeError("Neo4j environment variables are required.")

PROFILE_FILE = "data/processed/occupation_skill_profiles.csv"

OUTPUT_FILE = ("data/evaluation/semantic_skill_pairs_candidates.csv")

RANDOM_SEED = 42

STOPWORDS = {
    "use",
    "apply",
    "manage",
    "perform",
    "develop",
    "create",
    "maintain",
    "implement",
    "operate",
    "provide",
    "ensure",
    "analyse",
    "analysis",
    "system",
    "systems",
    "software",
    "technology",
    "technologies",
    "ict",
    "and",
    "of",
    "for",
    "to",
    "in",
    "with",
    "on",
    "the",
    "a",
    "an"
}


def load_analytical_occupation_ids():
    """
    Loads the 40 occupations belonging to the
    current analytical scope.
    """
    df = pd.read_csv(PROFILE_FILE)

    return (
        df["occupation_id"]
        .dropna()
        .drop_duplicates()
        .tolist()
    )


def load_canonical_skills(session, occupation_ids):
    """
    Loads the distinct canonical ESCO skills
    belonging to the analytical occupations.
    """
    result = session.run("""
        MATCH (o:Occupation)-[:ESCO_REQUIRES]->(s:Skill)

        WHERE o.esco_id IN $occupation_ids
          AND s.esco_id IS NOT NULL
          AND s.name IS NOT NULL

        RETURN DISTINCT
            s.esco_id AS skill_id,
            s.name AS skill_name

        ORDER BY skill_name
    """,
        occupation_ids=occupation_ids
    )

    return [
        {
            "skill_id": record["skill_id"],
            "skill_name": record["skill_name"]
        }
        for record in result
    ]


def make_pair_key(skill_a_id, skill_b_id):
    """
    Creates a direction-independent unique key
    for a pair of skills.
    """
    return tuple(sorted([skill_a_id, skill_b_id]))

def load_diverse_same_occupation_pairs(session, occupation_ids, max_pairs=40, max_skill_occurrences=3):
    """
    Creates diverse pairs of skills that occur
    in the same analytical occupation.

    Sampling is distributed across occupations
    so that one skill family does not dominate
    the validation dataset.
    """
    result = session.run("""
        MATCH (o:Occupation)-[:ESCO_REQUIRES]->(s1:Skill)
        MATCH (o)-[:ESCO_REQUIRES]->(s2:Skill)

        WHERE o.esco_id IN $occupation_ids
          AND s1.esco_id < s2.esco_id
          AND s1.name IS NOT NULL
          AND s2.name IS NOT NULL

        RETURN DISTINCT
            o.esco_id AS occupation_id,
            o.name AS occupation_name,

            s1.esco_id AS skill_a_id,
            s1.name AS skill_a,

            s2.esco_id AS skill_b_id,
            s2.name AS skill_b
    """,
        occupation_ids=occupation_ids
    )

    rows = [
        {
            "occupation_id": record["occupation_id"],
            "occupation_name": record["occupation_name"],
            "skill_a_id": record["skill_a_id"],
            "skill_a": record["skill_a"],
            "skill_b_id": record["skill_b_id"],
            "skill_b": record["skill_b"]
        }
        for record in result
    ]

    pairs_by_occupation = {}

    for row in rows:
        occupation_id = row["occupation_id"]
        pairs_by_occupation.setdefault(occupation_id, []).append(row)

    occupation_list = list(pairs_by_occupation.keys())

    random.shuffle(occupation_list)

    selected_pairs = []

    used_pairs = set()
    skill_occurrences = {}

    while len(selected_pairs) < max_pairs:
        added_in_round = False
        for occupation_id in occupation_list:
            candidates = (pairs_by_occupation[occupation_id].copy())

            random.shuffle(candidates)

            for candidate in candidates:
                pair_key = make_pair_key(candidate["skill_a_id"], candidate["skill_b_id"])

                if pair_key in used_pairs:
                    continue

                count_a = skill_occurrences.get(candidate["skill_a_id"], 0)
                count_b = skill_occurrences.get(candidate["skill_b_id"], 0)

                if (count_a >= max_skill_occurrences or count_b >= max_skill_occurrences):
                    continue

                selected_pairs.append({
                    "skill_a_id": candidate["skill_a_id"],
                    "skill_a": candidate["skill_a"],
                    "skill_b_id": candidate["skill_b_id"],
                    "skill_b": candidate["skill_b"],
                    "candidate_type": "same_occupation",
                    "occupation": candidate["occupation_name"],
                    "lexical_score": "",
                    "label": ""
                })

                used_pairs.add(pair_key)

                skill_occurrences[candidate["skill_a_id"]] = count_a + 1
                skill_occurrences[candidate["skill_b_id"]] = count_b + 1

                added_in_round = True

                break

            if len(selected_pairs) >= max_pairs:
                break

        if not added_in_round:
            break

    return selected_pairs


def normalize_skill_name(text):
    """
    Normalizes an ESCO skill label for lexical
    candidate generation.
    """
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    tokens = [
        token
        for token in text.split()
        if token not in STOPWORDS
    ]

    return " ".join(tokens)


def token_jaccard(text_a, text_b):
    """
    Calculates lexical token overlap.
    """
    tokens_a = set(normalize_skill_name(text_a).split())
    tokens_b = set(normalize_skill_name(text_b).split())

    if not tokens_a or not tokens_b:
        return 0.0

    intersection = len(tokens_a & tokens_b)
    union = len(tokens_a | tokens_b)

    return intersection / union


def lexical_similarity(text_a, text_b):
    """
    Produces a model-independent lexical similarity
    score.
    This score is used ONLY to generate likely
    positive candidates.
    It is NOT used as semantic coverage and does not
    become part of MatchESCO.
    """
    normalized_a = normalize_skill_name(text_a)
    normalized_b = normalize_skill_name(text_b)

    if not normalized_a or not normalized_b:
        return 0.0

    sequence_score = SequenceMatcher(None, normalized_a, normalized_b).ratio()

    jaccard_score = token_jaccard(text_a, text_b)

    return max(sequence_score, jaccard_score)


def generate_positive_candidates(skills, excluded_pairs, n=20, max_skill_occurrences=2):
    """
    Generates likely positive candidates using
    model-independent lexical similarity.

    IMPORTANT:
    These are only candidates.
    They are NOT automatically labelled as positive.

    Manual annotation will determine whether
    label = 1 or 0.
    """

    candidate_pairs = []

    for i in range(len(skills)):
        skill_a = skills[i]
        for j in range(i + 1, len(skills)):
            skill_b = skills[j]

            pair_key = make_pair_key(skill_a["skill_id"], skill_b["skill_id"])

            if pair_key in excluded_pairs:
                continue

            score = lexical_similarity(skill_a["skill_name"], skill_b["skill_name"])

            candidate_pairs.append({
                "skill_a_id": skill_a["skill_id"],
                "skill_a": skill_a["skill_name"],
                "skill_b_id": skill_b["skill_id"],
                "skill_b": skill_b["skill_name"],
                "lexical_score": score,
                "pair_key": pair_key
            })

    candidate_pairs.sort(
        key=lambda x: x["lexical_score"],
        reverse=True
    )

    selected = []

    skill_occurrences = {}

    for candidate in candidate_pairs:
        skill_a_id = candidate["skill_a_id"]
        skill_b_id = candidate["skill_b_id"]

        count_a = skill_occurrences.get(skill_a_id, 0)
        count_b = skill_occurrences.get(skill_b_id, 0)

        if (count_a >= max_skill_occurrences or count_b >= max_skill_occurrences):
            continue

        selected.append({
            "skill_a_id": skill_a_id,
            "skill_a": candidate["skill_a"],
            "skill_b_id": skill_b_id,
            "skill_b": candidate["skill_b"],
            "candidate_type": "positive_candidate",
            "occupation": "",
            "lexical_score":
                round(candidate["lexical_score"], 4),
            "label": ""
        })

        excluded_pairs.add(candidate["pair_key"])

        skill_occurrences[skill_a_id] = count_a + 1
        skill_occurrences[skill_b_id] = count_b + 1

        if len(selected) >= n:
            break

    return selected


def generate_random_pairs(skills, excluded_pairs, n=20):
    """
    Generates random skill pairs from the analytical
    canonical skill universe.

    These are expected to provide mostly easy
    negative examples, but labels remain manual.
    """
    pairs = []

    while len(pairs) < n:
        skill_a, skill_b = random.sample(skills, 2)

        pair_key = make_pair_key(skill_a["skill_id"], skill_b["skill_id"])
        if pair_key in excluded_pairs:
            continue
        excluded_pairs.add(pair_key)

        pairs.append({
            "skill_a_id": skill_a["skill_id"],
            "skill_a": skill_a["skill_name"],
            "skill_b_id": skill_b["skill_id"],
            "skill_b": skill_b["skill_name"],
            "candidate_type": "random",
            "occupation": "",
            "lexical_score": "",
            "label": ""
        })

    return pairs


def main():

    random.seed(RANDOM_SEED)

    occupation_ids = (load_analytical_occupation_ids())

    print("=" * 80)
    print("SEMANTIC VALIDATION PAIR GENERATION")
    print("=" * 80)

    print("Analytical occupations loaded:", len(occupation_ids))

    driver = GraphDatabase.driver(URI, auth=(USER, PASSWORD))

    with driver.session() as session:
        skills = load_canonical_skills(session, occupation_ids)

        same_occupation_pairs = (
            load_diverse_same_occupation_pairs(
                session,
                occupation_ids,
                max_pairs=40,
                max_skill_occurrences=3
            )
        )

    driver.close()

    print("Canonical skills loaded:", len(skills))

    print("Diverse same-occupation pairs:", len(same_occupation_pairs))

    used_pairs = {
        make_pair_key(
            pair["skill_a_id"],
            pair["skill_b_id"]
        )
        for pair in same_occupation_pairs
    }

    positive_candidates = (
        generate_positive_candidates(
            skills,
            used_pairs,
            n=50,
            max_skill_occurrences=3
        )
    )

    print("Positive candidate pairs:", len(positive_candidates))

    random_pairs = generate_random_pairs(skills, used_pairs, n=20)

    print("Random candidate pairs:", len(random_pairs))

    all_pairs = (same_occupation_pairs + positive_candidates + random_pairs)

    df = pd.DataFrame(all_pairs)

    df.to_csv(OUTPUT_FILE, index=False)

    print("\nCandidate pairs saved to:")
    print(OUTPUT_FILE)

    print("\nTotal candidate pairs:", len(df))
    print("\nCandidate type distribution:")
    print(
        df["candidate_type"]
        .value_counts()
        .to_string()
    )

if __name__ == "__main__":
    main()