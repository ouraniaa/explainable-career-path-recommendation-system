"""
Provides structural occupation similarity for the Career Transition workflow.

Instead of comparing the current occupation with every possible career directly, 
the module first identifies occupations with similar official ESCO skill structures.

Similarity is calculated with unweighted Jaccard over canonical ESCO skill sets. The
result is used only for candidate generation and structural explanation. It is not a
measure of user readiness, labor-market demand, or transition probability, and it does
not determine the final recommendation order, which is handled later with MatchESCO.
"""
def get_occupation_skill_neighbors(session, occupation_id):
    """
    Return the canonical ESCO skill set connected to one occupation.
    Only official ESCO_REQUIRES relations are used here. Job-posting relations are
    intentionally excluded so the structural comparison reflects the ESCO graph itself.
    """
    if not occupation_id:
        raise ValueError("occupation_id cannot be empty.")

    query = """
    MATCH (o:Occupation {esco_id: $occupation_id})

    OPTIONAL MATCH
        (o)-[:ESCO_REQUIRES]->(s:Skill)

    RETURN
        o.esco_id AS occupation_id,
        o.name AS occupation_name,
        o.isco_group AS isco_group,
        collect(DISTINCT s.esco_id) AS skill_ids
    """

    record = session.run(query, occupation_id=occupation_id).single()

    if record is None:
        raise ValueError(f"Occupation not found: {occupation_id}")

    skill_ids = {
        skill_id
        for skill_id in record["skill_ids"]
        if skill_id is not None
    }

    return {
        "occupation_id": record["occupation_id"],
        "occupation_name": record["occupation_name"],
        "isco_group": record["isco_group"],
        "skill_ids": skill_ids,
        "skill_count": len(skill_ids)
    }


def calculate_occupation_jaccard_similarity(session, occupation_a_id, occupation_b_id):
    """
    Compare two occupations with unweighted Jaccard similarity over their ESCO skill sets.
    The score only describes how much canonical skill structure the occupations share.
    """
    if occupation_a_id == occupation_b_id:
        raise ValueError("The two occupations must be different.")

    occupation_a = (get_occupation_skill_neighbors(session=session, occupation_id=occupation_a_id))

    occupation_b = (get_occupation_skill_neighbors(session=session, occupation_id=occupation_b_id))

    skills_a = occupation_a["skill_ids"]
    skills_b = occupation_b["skill_ids"]

    intersection = (skills_a.intersection(skills_b))
    union = (skills_a.union(skills_b))

    if not union:
        similarity = None
        reason = ("Jaccard similarity is undefined because both occupations have empty canonical ESCO skill neighborhoods.")
    else:
        similarity = (len(intersection) / len(union))
        reason = None

    return {
        "occupation_a_id": occupation_a["occupation_id"],
        "occupation_a_name": occupation_a["occupation_name"],
        "occupation_a_isco_group": occupation_a["isco_group"],
        "occupation_a_skill_count": occupation_a["skill_count"],
        "occupation_b_id": occupation_b["occupation_id"], 
        "occupation_b_name": occupation_b["occupation_name"],
        "occupation_b_isco_group": occupation_b["isco_group"],
        "occupation_b_skill_count": occupation_b["skill_count"],
        "shared_skill_count": len(intersection),
        "union_skill_count": len(union),
        "shared_skill_ids": sorted(intersection),
        "jaccard_similarity": similarity,
        "reason": reason
    }


def get_ict_candidate_occupations(session):
    """
    Return the ICT occupation pool used to generate Career Transition candidates.

    The scope includes ISCO 25xx, 35xx, and 1330. 
    """
    query = """
    MATCH (o:Occupation)

    WHERE
        o.isco_group STARTS WITH '25'
        OR o.isco_group STARTS WITH '35'
        OR o.isco_group = '1330'

    OPTIONAL MATCH
        (o)-[:ESCO_REQUIRES]->(s:Skill)

    WITH
        o,
        collect(DISTINCT s.esco_id) AS skill_ids

    RETURN
        o.esco_id AS occupation_id,
        o.name AS occupation_name,
        o.isco_group AS isco_group,
        skill_ids
    ORDER BY
        occupation_name,
        occupation_id
    """
    records = session.run(query)
    occupations = []

    for record in records:
        skill_ids = {
            skill_id
            for skill_id in record["skill_ids"]
            if skill_id is not None
        }

        occupations.append({
            "occupation_id": record["occupation_id"],
            "occupation_name": record["occupation_name"],
            "isco_group": record["isco_group"],
            "skill_ids": skill_ids,
            "skill_count": len(skill_ids)
        })

    return occupations


def find_similar_occupations(session, current_occupation_id, top_n=10, min_shared_skills=1):
    """
    Find the most structurally similar ICT occupations to the user's current occupation.

    The function builds the transition candidate set by comparing canonical ESCO skill
    neighborhoods with unweighted Jaccard similarity.
    """
    if type(top_n) is not int or top_n <= 0:
        raise ValueError("top_n must be a positive integer.")

    if (type(min_shared_skills) is not int or min_shared_skills < 0):
        raise ValueError("min_shared_skills must be a non-negative integer."
        )

    current_occupation = (get_occupation_skill_neighbors(session=session, occupation_id=current_occupation_id))
    current_skills = (current_occupation["skill_ids"])
    candidate_occupations = (get_ict_candidate_occupations(session=session))

    results = []

    for candidate in candidate_occupations:
        candidate_id = (candidate["occupation_id"])

        if candidate_id == current_occupation_id:
            continue
        candidate_skills = (candidate["skill_ids"])
        shared_skills = (current_skills.intersection(candidate_skills))
        shared_skill_count = (len(shared_skills))

        if (shared_skill_count < min_shared_skills):
            continue

        union_skills = (current_skills.union(candidate_skills))

        if not union_skills:
            continue

        jaccard_similarity = (shared_skill_count / len(union_skills))

        results.append({
            "occupation_id": candidate_id,
            "occupation_name": candidate["occupation_name"],
            "isco_group":
                candidate[
                    "isco_group"
                ],

            "current_occupation_skill_count": len(current_skills),
            "candidate_skill_count": len(candidate_skills),
            "shared_skill_count": shared_skill_count,
            "union_skill_count": len(union_skills),
            "jaccard_similarity": jaccard_similarity,
            "shared_skill_ids": sorted(shared_skills)
        })

    results.sort(
        key=lambda item: (
            -item["jaccard_similarity"],
            -item["shared_skill_count"],
            item["occupation_name"] or "",
            item["occupation_id"]
        )
    )

    top_results = results[:top_n]

    ranked_results = []

    for rank, item in enumerate(top_results, start=1):
        ranked_item = {
            "rank": rank, **item
        }

        ranked_results.append(ranked_item)

    return {
        "current_occupation_id": current_occupation["occupation_id"],
        "current_occupation_name": current_occupation["occupation_name"],
        "current_occupation_isco_group": current_occupation["isco_group"],
        "current_occupation_skill_count": current_occupation["skill_count"],
        "candidate_pool_definition":
            [
                "25xx",
                "35xx",
                "1330"
            ],

        "similarity_method": "unweighted_jaccard", 
        "candidate_count_before_filtering": len(candidate_occupations),
        "candidate_count_after_filtering": len(results),
        "min_shared_skills": min_shared_skills,
        "requested_top_n": top_n,
        "returned_count": len(ranked_results),
        "similar_occupations": ranked_results
    }