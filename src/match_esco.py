"""
Calculates the main ESCO-based skill match between a user profile and an occupation.

This file was created because exact skill-ID matching alone was too strict for the thesis:
a user may select a skill that is closely related to an occupation requirement without
having the exact same ESCO identifier. To handle that case, this file keeps exact matches
at full coverage and adds partial semantic coverage when the best MPNet similarity passes
the configured threshold.

The calculation uses only the occupation's canonical ESCO requirements. Semantic matching
is used as partial evidence, not as proof that the user already possesses the required
skill.
"""
import numpy as np
import pandas as pd

EMBEDDINGS_FILE = ("data/processed/skill_embeddings_mpnet.npy")
INDEX_FILE = ("data/processed/skill_embeddings_index.csv")

SEMANTIC_THRESHOLD = 0.64

def load_embedding_cache():
    """
    Load the precomputed MPNet embeddings and map each ESCO skill ID to its vector.
    The cache is prepared in advance so semantic comparisons do not need to recreate
    embeddings every time an occupation is evaluated.
    """
    embeddings = np.load(EMBEDDINGS_FILE)

    index_df = pd.read_csv(INDEX_FILE)

    if len(index_df) != len(embeddings):
        raise ValueError("Embedding index and embedding matrix have different sizes.")

    embedding_lookup = {}

    for _, row in index_df.iterrows():
        skill_id = row["skill_id"]
        embedding_index = int(row["embedding_index"])

        embedding_lookup[skill_id] = embeddings[embedding_index]

    return embedding_lookup

EMBEDDING_LOOKUP = (load_embedding_cache())


def get_occupation_skills(session, occupation_id):
    """
    Return the canonical ESCO skills required by the target occupation.
    These ESCO_REQUIRES relations define the requirement set used by MatchESCO.
    """
    result = session.run("""
        MATCH (o:Occupation {esco_id: $occupation_id})
              -[r:ESCO_REQUIRES]->
              (s:Skill)

        RETURN
            s.esco_id AS skill_id,
            s.name AS skill_name,
            r.relation_type AS relation_type

        ORDER BY s.name
    """,
        occupation_id=occupation_id
    )

    return [
        {
            "skill_id": record["skill_id"],
            "skill_name": record["skill_name"],
            "relation_type": record["relation_type"]
        }
        for record in result
    ]


def get_user_skills(session, user_skill_ids):
    """
    Load the names of the user's selected ESCO skills from Neo4j.
    The names are kept mainly for explainability, so the final result can show which
    selected skill produced an exact or semantic match.
    """
    result = session.run("""
        MATCH (s:Skill)

        WHERE s.esco_id IN $user_skill_ids

        RETURN
            s.esco_id AS skill_id,
            s.name AS skill_name
    """,
        user_skill_ids=list(user_skill_ids)
    )

    return {
        record["skill_id"]:
            record["skill_name"]

        for record in result
    }


def cosine_similarity(embedding_a, embedding_b):
    """
    Calculate cosine similarity between two normalized embedding vectors.
    Because the cached embeddings are already normalized, their dot product is the
    cosine similarity.
    """
    return float(np.dot(embedding_a, embedding_b))


def find_best_semantic_match(required_skill_id, user_skill_ids):
    """
    Find the user's selected skill that is semantically closest to one required ESCO skill.

    The function returns the best matching skill ID and its raw similarity. If an embedding
    is unavailable, no semantic match can be evaluated for that requirement.
    """
    required_embedding = (EMBEDDING_LOOKUP.get(required_skill_id))

    if required_embedding is None:
        return None, 0.0

    best_user_skill_id = None
    best_similarity = 0.0

    for user_skill_id in user_skill_ids:
        user_embedding = (EMBEDDING_LOOKUP.get(user_skill_id))

        if user_embedding is None:
            continue

        similarity = cosine_similarity(required_embedding, user_embedding)

        if similarity > best_similarity:
            best_similarity = similarity
            best_user_skill_id = (user_skill_id)

    return (best_user_skill_id, best_similarity)

def calculate_match_esco(session, occupation_id, user_skill_ids):
    """
    Exact ESCO skill matches receive full coverage. When there is no exact match, the
    function checks the closest semantic match from the user's selected skills. Semantic
    similarity contributes partial coverage only when it reaches the configured threshold.
    """
    user_skill_ids = set(user_skill_ids)

    occupation_skills = get_occupation_skills(session, occupation_id)

    user_skill_names = get_user_skills(session, user_skill_ids)

    if not occupation_skills:
        return {
            "occupation_id": occupation_id,
            "match_esco": None,
            "canonical_skill_count": 0,
            "exact_match_count": 0,
            "semantic_match_count": 0,
            "covered_skill_count": 0,
            "details": []
        }

    details = []

    total_coverage = 0.0
    exact_match_count = 0
    semantic_match_count = 0

    for required_skill in occupation_skills:
        required_skill_id = (required_skill["skill_id"])
        required_skill_name = (required_skill["skill_name"])
        if required_skill_id in user_skill_ids:
            coverage = 1.0
            match_type = "exact"

            best_user_skill_id = (required_skill_id)
            best_user_skill_name = (user_skill_names.get(required_skill_id, required_skill_name))

            raw_similarity = 1.0
            exact_match_count += 1
        else:
            (best_user_skill_id, raw_similarity) = find_best_semantic_match(required_skill_id, user_skill_ids)

            if (best_user_skill_id is not None and raw_similarity >= SEMANTIC_THRESHOLD):
                coverage = raw_similarity
                match_type = "semantic"

                best_user_skill_name = (user_skill_names.get(best_user_skill_id))

                semantic_match_count += 1
            else:
                coverage = 0.0
                match_type = "none"

                best_user_skill_name = (user_skill_names.get(best_user_skill_id)
                    if best_user_skill_id
                    else None
                )

        total_coverage += coverage

        details.append({
            "required_skill_id": required_skill_id,
            "required_skill_name": required_skill_name,
            "relation_type": required_skill["relation_type"],
            "best_user_skill_id": best_user_skill_id,
            "best_user_skill_name": best_user_skill_name,
            "raw_similarity": float(raw_similarity),
            "coverage": float(coverage),
            "match_type": match_type
        })

    canonical_skill_count = len(occupation_skills)
    match_esco = (total_coverage / canonical_skill_count)
    covered_skill_count = (exact_match_count + semantic_match_count)

    return {
        "occupation_id": occupation_id,
        "match_esco": match_esco,
        "canonical_skill_count": canonical_skill_count,
        "exact_match_count": exact_match_count,
        "semantic_match_count": semantic_match_count,
        "covered_skill_count": covered_skill_count,
        "semantic_threshold": SEMANTIC_THRESHOLD,
        "details": details
    }

def calculate_skill_coverage(required_skill_id, user_skill_ids):
    """
    Calculate the coverage of one required ESCO skill for the current user profile.

    This helper applies the same exact-first and thresholded semantic logic used by
    MatchESCO and is reused by other modules that need skill-level coverage.
    """
    user_skill_ids = set(user_skill_ids)

    if required_skill_id in user_skill_ids:
        return 1.0

    best_user_skill_id, similarity = (find_best_semantic_match(required_skill_id, user_skill_ids))

    if (best_user_skill_id is not None and similarity >= SEMANTIC_THRESHOLD):
        return float(similarity)

    return 0.0