"""
Provides graph-based skill similarity using the ESCO knowledge graph.

The module compares skills by looking at the occupations that require them through
ESCO_REQUIRES relationships. Skills that appear in similar occupation neighborhoods
receive a higher unweighted Jaccard similarity score.

This is used only as structural graph evidence and for finding related skills. It is
not a semantic similarity model and it does not change the main ESCO matching score.
"""
def get_skill_occupation_neighbors(session, skill_id):
    if not skill_id:
        raise ValueError("skill_id cannot be empty.")

    query = """
    MATCH (s:Skill {esco_id: $skill_id})

    OPTIONAL MATCH
        (o:Occupation)-[:ESCO_REQUIRES]->(s)

    RETURN
        s.esco_id AS skill_id,
        s.name AS skill_name,
        collect(DISTINCT o.esco_id) AS occupation_ids
    """
    record = session.run(query, skill_id=skill_id).single()

    if record is None:
        raise ValueError(f"Skill not found in Neo4j: {skill_id}")

    occupation_ids = {
        occupation_id
        for occupation_id in record["occupation_ids"]
        if occupation_id is not None
    }

    return {
        "skill_id": record["skill_id"],
        "skill_name": record["skill_name"],
        "occupation_ids": occupation_ids,
        "occupation_count": len(occupation_ids)
    }


def calculate_jaccard_similarity(
    session,
    skill_a_id,
    skill_b_id
):
    """
    Compare two skills using Jaccard similarity over their ESCO occupation neighborhoods.
    """

    if not skill_a_id:
        raise ValueError("skill_a_id cannot be empty.")

    if not skill_b_id:
        raise ValueError("skill_b_id cannot be empty.")

    skill_a = get_skill_occupation_neighbors(session=session, skill_id=skill_a_id)
    skill_b = get_skill_occupation_neighbors(session=session, skill_id=skill_b_id)

    neighbors_a = skill_a["occupation_ids"]
    neighbors_b = skill_b["occupation_ids"]

    shared_occupations = (neighbors_a.intersection(neighbors_b))

    union_occupations = (neighbors_a.union(neighbors_b))

    intersection_count = len(shared_occupations)

    union_count = len(union_occupations)

    if union_count == 0:
        jaccard_similarity = None

        reason = (
            "No ESCO occupation neighbors are available "
            "for either skill."
        )
    else:
        jaccard_similarity = (intersection_count / union_count)

        reason = None

    return {
        "skill_a_id": skill_a["skill_id"],
        "skill_a_name": skill_a["skill_name"],

        "skill_b_id": skill_b["skill_id"],
        "skill_b_name": skill_b["skill_name"],

        "skill_a_occupation_count": skill_a["occupation_count"],
        "skill_b_occupation_count": skill_b["occupation_count"],

        "shared_occupation_count": intersection_count, 
        "union_occupation_count": union_count,
        "shared_occupation_ids": sorted(shared_occupations),
        "jaccard_similarity": jaccard_similarity,
        "reason": reason
    }

def get_multiple_skill_occupation_neighbors(session, skill_ids):
    """
    Retrieve the occupation neighborhoods for multiple skills in one Neo4j query.

    This avoids running one separate graph query for every candidate skill when many
    similarities need to be evaluated.
    """

    if not skill_ids:
        return {}

    unique_skill_ids = list(dict.fromkeys(skill_ids))

    query = """
    MATCH (s:Skill)
    WHERE s.esco_id IN $skill_ids

    OPTIONAL MATCH
        (o:Occupation)-[:ESCO_REQUIRES]->(s)

    RETURN
        s.esco_id AS skill_id,
        s.name AS skill_name,
        collect(DISTINCT o.esco_id) AS occupation_ids
    """

    records = session.run(query, skill_ids=unique_skill_ids)

    results = {}

    for record in records:
        occupation_ids = {
            occupation_id
            for occupation_id in record["occupation_ids"]
            if occupation_id is not None
        }

        results[record["skill_id"]] = {
            "skill_id": record["skill_id"],
            "skill_name": record["skill_name"],
            "occupation_ids": occupation_ids,
            "occupation_count": len(occupation_ids)
        }

    return results


def find_related_skills(
    session,
    skill_id,
    candidate_skill_ids,
    top_n=10,
    min_shared_occupations=1
):
    """
    Rank candidate skills by unweighted Jaccard similarity to a target skill.

    Candidates must share the requested minimum number of occupations with the target.
    The threshold is only a filter; it does not alter the Jaccard score itself.
    """
    if not skill_id:
        raise ValueError("skill_id cannot be empty.")

    if type(top_n) is not int or top_n <= 0:
        raise ValueError("top_n must be a positive integer.")

    if (type(min_shared_occupations) is not int or min_shared_occupations < 1):
        raise ValueError("min_shared_occupations must be a positive integer.")

    candidate_skill_ids = [
        candidate_id
        for candidate_id in dict.fromkeys(candidate_skill_ids)
        if candidate_id != skill_id
    ]

    target = get_skill_occupation_neighbors(session=session, skill_id=skill_id)

    target_neighbors = target["occupation_ids"]

    if not target_neighbors:
        return {
            "skill_id": target["skill_id"],
            "skill_name": target["skill_name"],
            "occupation_count": 0,
            "candidate_count": len(candidate_skill_ids),
            "related_skill_count": 0,
            "related_skills": [],
            "reason": (
                "Target skill has no ESCO occupation "
                "neighbors."
            )
        }

    candidate_lookup = (get_multiple_skill_occupation_neighbors(session=session, skill_ids=candidate_skill_ids))

    related_skills = []

    for candidate_id in candidate_skill_ids:
        candidate = candidate_lookup.get(candidate_id)

        if candidate is None:
            continue

        candidate_neighbors = candidate["occupation_ids"]

        if not candidate_neighbors:
            continue

        shared_occupations = (target_neighbors & candidate_neighbors)

        shared_count = len(shared_occupations)

        if (shared_count < min_shared_occupations):
            continue

        union_occupations = (target_neighbors | candidate_neighbors)
        union_count = len(union_occupations)

        if union_count == 0:
            continue

        jaccard_similarity = (shared_count / union_count)

        related_skills.append({
            "skill_id": candidate["skill_id"],
            "skill_name": candidate["skill_name"],
            "jaccard_similarity": jaccard_similarity,
            "shared_occupation_count": shared_count,
            "union_occupation_count": union_count,
            "candidate_occupation_count": candidate["occupation_count"],
            "shared_occupation_ids": sorted(shared_occupations)
        })

    related_skills.sort(
        key=lambda item: (
            -item["jaccard_similarity"],
            -item["shared_occupation_count"],
            item["skill_name"].lower(),
            item["skill_id"]
        )
    )

    related_skills = (related_skills[:top_n])

    for index, item in enumerate(related_skills, start=1):
        item["rank"] = index

    return {
        "skill_id": target["skill_id"],
        "skill_name": target["skill_name"],
        "occupation_count": target["occupation_count"],
        "candidate_count": len(candidate_skill_ids),
        "related_skill_count": len(related_skills),
        "ranking_criterion": "jaccard_similarity",
        "min_shared_occupations": min_shared_occupations,
        "related_skills": related_skills,
        "reason": None
    }

def find_related_skills_for_skill(session, skill_id, top_n=5, min_shared_occupations=1):
    """
    Find related skills directly from the knowledge graph.

    Candidate skills are first discovered through shared ESCO occupations, then the
    existing Jaccard logic is used to rank them by structural similarity.
    """

    if not skill_id:
        raise ValueError("skill_id cannot be empty.")

    if type(top_n) is not int or top_n <= 0:
        raise ValueError("top_n must be a positive integer.")

    query = """
    MATCH
        (target:Skill {esco_id: $skill_id})

    MATCH
        (o:Occupation)-[:ESCO_REQUIRES]->(target)

    MATCH
        (o)-[:ESCO_REQUIRES]->(candidate:Skill)

    WHERE
        candidate.esco_id <> target.esco_id

    RETURN DISTINCT
        candidate.esco_id AS skill_id
    """

    records = session.run(query, skill_id=skill_id)

    candidate_skill_ids = [
        record["skill_id"]
        for record in records
        if record["skill_id"] is not None
    ]

    return find_related_skills(
        session=session,
        skill_id=skill_id,
        candidate_skill_ids=candidate_skill_ids,
        top_n=top_n,
        min_shared_occupations=min_shared_occupations
    )