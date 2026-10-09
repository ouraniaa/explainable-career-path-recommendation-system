"""
Creates deterministic explanations for graph-based skill and occupation similarity.

The graph modules calculate Jaccard similarity and shared-neighborhood statistics first;
this module only turns those existing values into readable explanations.

For skills, structural relatedness is explained through shared ESCO occupation
neighborhoods. For occupations, similarity is explained through shared canonical ESCO
skills.
"""
def generate_skill_graph_explanation(skill_graph_result):
    """
    Explains why other skills are structurally related to a selected skill.
    """
    if not isinstance(skill_graph_result, dict):
        raise ValueError("skill_graph_result must be a dictionary.")

    required_fields = {
        "skill_id",
        "skill_name",
        "occupation_count",
        "ranking_criterion",
        "related_skills"
    }

    missing_fields = (required_fields - set(skill_graph_result.keys()))

    if missing_fields:
        raise ValueError("skill_graph_result is missing required fields: "
            f"{sorted(missing_fields)}"
        )

    related_skills = skill_graph_result["related_skills"]

    skill_name = skill_graph_result["skill_name"]
    skill_occupation_count = skill_graph_result["occupation_count"]

    general_explanation = (
        f"The skill '{skill_name}' appears as a canonical "
        f"ESCO requirement in {skill_occupation_count} occupations. Structural relatedness with other skills is measured using unweighted Jaccard similarity over shared occupation neighborhoods."
    )

    explained_related_skills = []

    for item in related_skills:
        required_item_fields = {
            "rank",
            "skill_id",
            "skill_name",
            "jaccard_similarity",
            "shared_occupation_count",
            "union_occupation_count"
        }

        missing_item_fields = (required_item_fields - set(item.keys()))

        if missing_item_fields:
            raise ValueError(
                f"Related skill result is missing fields: "
                f"{sorted(missing_item_fields)}"
            )
        
        jaccard_percent = (item["jaccard_similarity"] * 100)

        explanation_text = (
            f"'{item['skill_name']}' is structurally related "
            f"to '{skill_name}' because the two skills occur "
            f"as canonical ESCO requirements in "
            f"{item['shared_occupation_count']} shared "
            f"occupations. Across both occupation "
            f"neighborhoods there are "
            f"{item['union_occupation_count']} distinct "
            f"occupations, producing a Jaccard similarity "
            f"of {jaccard_percent:.2f}%."
        )

        explained_related_skills.append({
            "rank": item["rank"],
            "skill_id": item["skill_id"],
            "skill_name": item["skill_name"],
            "jaccard_similarity": item["jaccard_similarity"],
            "jaccard_percent": jaccard_percent,
            "shared_occupation_count": item["shared_occupation_count"],
            "union_occupation_count": item["union_occupation_count"],
            "explanation_text": explanation_text
        })

    return {
        "explanation_type": "skill_graph", 
        "skill_id": skill_graph_result["skill_id"],
        "skill_name": skill_name,
        "occupation_count": skill_occupation_count,
        "ranking_criterion": skill_graph_result["ranking_criterion"],
        "general_explanation": general_explanation,
        "related_skills": explained_related_skills
    }


def generate_occupation_graph_explanation(occupation_similarity_result):
    """
    Explains why other occupations are structurally similar to the current occupation.
    """
    if not isinstance(occupation_similarity_result, dict):
        raise ValueError("occupation_similarity_result must be a dictionary.")

    required_fields = {
        "current_occupation_id",
        "current_occupation_name",
        "current_occupation_isco_group",
        "current_occupation_skill_count",
        "similarity_method",
        "similar_occupations"
    }

    missing_fields = (required_fields - set(occupation_similarity_result.keys()))

    if missing_fields:
        raise ValueError("occupation_similarity_result is missing "
            f"required fields: {sorted(missing_fields)}"
        )

    similar_occupations = (occupation_similarity_result["similar_occupations"])
    current_occupation_name = (occupation_similarity_result["current_occupation_name"])
    current_skill_count = (occupation_similarity_result["current_occupation_skill_count"])
    general_explanation = (
        f"The current occupation "
        f"'{current_occupation_name}' has "
        f"{current_skill_count} canonical ESCO skills. "
        f"Related occupations are identified by comparing "
        f"their canonical ESCO skill sets using unweighted "
        f"Jaccard similarity."
    )

    explained_occupations = []

    for item in similar_occupations:
        required_item_fields = {
            "rank",
            "occupation_id",
            "occupation_name",
            "isco_group",
            "candidate_skill_count",
            "shared_skill_count",
            "union_skill_count",
            "jaccard_similarity"
        }

        missing_item_fields = (required_item_fields - set(item.keys()))

        if missing_item_fields:
            raise ValueError("Similar occupation result is missing fields: "
                f"{sorted(missing_item_fields)}"
            )

        jaccard_percent = (item["jaccard_similarity"] * 100)

        explanation_text = (
            f"'{item['occupation_name']}' is structurally "
            f"related to '{current_occupation_name}' because the two occupations share "
            f"{item['shared_skill_count']} canonical ESCO skills. Across their combined canonical profiles there are "
            f"{item['union_skill_count']} distinct skills, resulting in a Jaccard similarity of "
            f"{jaccard_percent:.2f}%."
        )

        explained_occupations.append({
            "rank": item["rank"], 
            "occupation_id": item["occupation_id"],
            "occupation_name": item["occupation_name"],
            "isco_group": item["isco_group"],
            "candidate_skill_count": item["candidate_skill_count"],
            "shared_skill_count": item["shared_skill_count"],
            "union_skill_count": item["union_skill_count"],
            "jaccard_similarity": item["jaccard_similarity"],
            "jaccard_percent": jaccard_percent,
            "explanation_text": explanation_text
        })

    return {
        "explanation_type": "occupation_graph",
        "current_occupation_id": occupation_similarity_result["current_occupation_id"],
        "current_occupation_name": current_occupation_name,
        "current_occupation_isco_group": occupation_similarity_result["current_occupation_isco_group"],
        "current_occupation_skill_count": current_skill_count,
        "similarity_method": occupation_similarity_result["similarity_method"],
        "general_explanation": general_explanation,
        "similar_occupations": explained_occupations
    }