"""
Builds personalized skill recommendations by combining learning impact with graph context.

This module was created because a pure learning-priority list explains which skill could
improve MatchESCO, but it does not show how that skill is connected to the wider ESCO
knowledge graph. To make the recommendation more informative, the module combines the
existing ImprovementESCO-based priority with related-skill graph evidence.

The graph information is explanatory only. It helps show structurally related skills and
occupation context, but it does not change the learning-priority ranking or introduce a
new combined score.
"""
from src.learning_priority import (calculate_learning_priority)
from src.graph_skill_similarity import (find_related_skills_for_skill)

def generate_personalized_skill_recommendations(session, occupation_id, user_skill_ids, top_n=5, graph_top_n=3):
    """
    Generates personalized skill recommendations
    for one target occupation.
    Main ranking criterion: ImprovementESCO
    """
    if type(top_n) is not int or top_n <= 0:
        raise ValueError("top_n must be a positive integer.")

    if type(graph_top_n) is not int or graph_top_n <= 0:
        raise ValueError("graph_top_n must be a positive integer.")

    priority_result = calculate_learning_priority(
        session = session,
        occupation_id=occupation_id,
        user_skill_ids=user_skill_ids,
        top_n=top_n
    )

    recommendations = []

    for item in priority_result["ranked_skills"]:
        explanation_parts = []
        relation_type = item["relation_type"]

        if relation_type:
            explanation_parts.append(f"ESCO classification: {relation_type}.")

        explanation_parts.append(
            "Current coverage: "
            f"{item['current_coverage']:.4f}; "
            "residual gap: "
            f"{item['residual_gap']:.4f}."
        )

        explanation_parts.append(
            "Expected MatchESCO improvement: "
            f"{item['improvement_esco'] * 100:.4f} "
            "percentage points."
        )

        explanation_parts.append(
            "Direct improvement: "
            f"{item['direct_improvement'] * 100:.4f} "
            "percentage points; "
            "semantic spillover: "
            f"{item['semantic_spillover'] * 100:.4f} "
            "percentage points."
        )

        if item["improvement_esco"] > 0.0:
            explanation_parts.append(
                "Semantic dependency ratio: "
                f"{item['semantic_dependency_ratio']:.4f}. "
                "This value is explanatory and does not "
                "affect the ranking."
            )

        if item["rca"] is not None:
            explanation_parts.append(
                "This skill has direct occupation-specific labor-market evidence. RCA: "
                f"{item['rca']:.4f}; "
                "Market Gap Severity: "
                f"{item['market_gap_severity']:.4f}."
            )
        else:
            explanation_parts.append(
                "No direct RCA value is available for this candidate skill in the target occupation."
            )

        if item["improvement_market"] is not None:
            if item["improvement_market"] > 0.0:
                if item["rca"] is not None:
                    explanation_parts.append(
                        "Expected MatchMarket improvement: "
                        f"{item['improvement_market'] * 100:.4f} "
                        "percentage points."
                    )
                else:
                    explanation_parts.append(
                        "Expected MatchMarket improvement: "
                        f"{item['improvement_market'] * 100:.4f} "
                        "percentage points. This improvement does not come from a direct RCA value for the candidate skill, but from improved coverage of other BOTH skills that have labor-market evidence."
                    )

            else:
                explanation_parts.append(
                    "No improvement in MatchMarket is expected from acquiring this skill under the current matching model."
                )
        else:
            explanation_parts.append(
                "MatchMarket improvement is not available because the target occupation does not have sufficient labor-market evidence."
            )

        affected_count = item["affected_esco_skill_count"]

        explanation_parts.append(
            "The hypothetical acquisition of this skill "
            f"improves coverage for {affected_count} canonical ESCO skill(s) according to the current matching model."
        )

        graph_result = find_related_skills_for_skill(
            session=session,
            skill_id=item["skill_id"],
            top_n=graph_top_n,
            min_shared_occupations=1
        )

        structurally_related_skills = []

        for related in graph_result["related_skills"]:
            structurally_related_skills.append({
                "rank": related["rank"], 
                "skill_id": related["skill_id"],
                "skill_name": related["skill_name"],
                "jaccard_similarity": related["jaccard_similarity"],
                "shared_occupation_count": related["shared_occupation_count"],
                "union_occupation_count": related["union_occupation_count"]
            })

        if structurally_related_skills:
            top_related = (structurally_related_skills[0])

            explanation_parts.append(
                "Graph-based structural analysis identified "
                f"'{top_related['skill_name']}' as the most "
                "closely related skill based on shared ESCO "
                "occupational contexts. "
                "Jaccard similarity: "
                f"{top_related['jaccard_similarity']:.4f}; "
                "shared occupations: "
                f"{top_related['shared_occupation_count']}. "
                "This graph-based signal is explanatory and does not affect the recommendation ranking."
            )

        else:
            explanation_parts.append(
                "No structurally related skills with shared ESCO occupational contexts were identified."
            )

        recommendations.append({
            "rank": item["rank"],
            "skill_id": item["skill_id"],
            "skill_name": item["skill_name"],
            "recommendation_type": "canonical_esco_skill",
            "relation_type": item["relation_type"],
            "current_coverage": item["current_coverage"],
            "residual_gap": item["residual_gap"],
            "improvement_esco": item["improvement_esco"],
            "direct_improvement": item["direct_improvement"],
            "semantic_spillover": item["semantic_spillover"],
            "semantic_dependency_ratio": item["semantic_dependency_ratio"],
            "rca": item["rca"],
            "market_gap_severity": item["market_gap_severity"],
            "improvement_market": item["improvement_market"],
            "affected_esco_skill_count": item["affected_esco_skill_count"],
            "affected_esco_skills": item["affected_esco_skills"],
            "affected_market_skills": item["affected_market_skills"],
            "structurally_related_skills": structurally_related_skills,
            "explanation": " ".join(explanation_parts)
        })

    return {
        "occupation_id": occupation_id,
        "current_match_esco": priority_result["current_match_esco"],
        "current_match_market": priority_result["current_match_market"],
        "canonical_skill_count": priority_result["canonical_skill_count"],
        "total_candidate_skills": priority_result["total_candidate_skills"],
        "ranking_criterion": priority_result["ranking_criterion"],
        "graph_similarity_method": "unweighted_jaccard",
        "graph_signal_role": "explanatory_only",
        "recommendation_count": len(recommendations),
        "recommendations": recommendations
    }