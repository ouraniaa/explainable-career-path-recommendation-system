"""
Creates an overall explanation by combining outputs that have
already been produced by the individual explainability modules.

This file's role is only to aggregate existing Job Match, Skill Gap, Career 
Path, and Graph explanations into one coherent summary.
"""


def generate_overall_explanation(job_match_explanation=None, skill_gap_explanation=None, career_path_explanation=None, graph_explanation=None):
    """
    Combines already generated explanation outputs into a single deterministic overall explanation.
    """
    explanations = {
        "job_match": job_match_explanation,
        "skill_gap": skill_gap_explanation,
        "career_path": career_path_explanation,
        "graph": graph_explanation
    }

    provided_explanations = {
        key: value
        for key, value in explanations.items()
        if value is not None
    }

    if not provided_explanations:
        raise ValueError("At least one explanation must be provided.")

    for name, explanation in provided_explanations.items():
        if not isinstance(explanation, dict):
            raise ValueError(f"{name} explanation must be a dictionary.")

    job_match_summary = None

    if job_match_explanation is not None:
        required_fields = {
            "explanation_type",
            "occupation_name",
            "match_esco_percent",
            "canonical_skill_count",
            "exact_match_count",
            "semantic_match_count",
            "missing_skill_count",
            "market_available"
        }

        missing_fields = (required_fields - set(job_match_explanation.keys()))

        if missing_fields:
            raise ValueError("job_match_explanation is missing fields: "
                f"{sorted(missing_fields)}"
            )

        if (job_match_explanation["explanation_type"] != "job_match"):
            raise ValueError("Expected a job_match explanation.")

        occupation_name = (job_match_explanation["occupation_name"])

        job_match_summary = (
            f"For the target occupation "
            f"'{occupation_name}', the user's current "
            f"skill profile achieves a MatchESCO of "
            f"{job_match_explanation['match_esco_percent']:.2f}%. "
            f"The canonical ESCO profile contains "
            f"{job_match_explanation['canonical_skill_count']} "
            f"skills, including "
            f"{job_match_explanation['exact_match_count']} "
            f"exactly matched skills and "
            f"{job_match_explanation['semantic_match_count']} "
            f"semantic matches. "
            f"{job_match_explanation['missing_skill_count']} "
            f"canonical skills currently have no coverage "
            f"under the matching criterion."
        )

        if (job_match_explanation["market_available"] and job_match_explanation["match_market_percent"] is not None):
            job_match_summary += (
                f" MatchMarket is "
                f"{job_match_explanation['match_market_percent']:.2f}% "
                f"and is reported separately as a "
                f"supplementary labor-market signal."
            )
        else:
            job_match_summary += (" MatchMarket is not available for this case and does not affect MatchESCO.")

    skill_gap_summary = None

    if skill_gap_explanation is not None:
        required_fields = {
            "explanation_type",
            "skill_name",
            "relation_type",
            "residual_gap_percent",
            "improvement_esco_percent",
            "direct_improvement_percent",
            "semantic_spillover_percent"
        }

        missing_fields = (required_fields - set(skill_gap_explanation.keys()))

        if missing_fields:
            raise ValueError("skill_gap_explanation is missing fields: "
                f"{sorted(missing_fields)}"
            )

        if (skill_gap_explanation["explanation_type"] != "skill_gap"):
            raise ValueError("Expected a skill_gap explanation.")

        skill_gap_summary = (
            f"The highlighted learning-priority skill is "
            f"'{skill_gap_explanation['skill_name']}', "
            f"classified as "
            f"'{skill_gap_explanation['relation_type']}' "
            f"in the canonical ESCO profile. "
            f"Its current residual gap is "
            f"{skill_gap_explanation['residual_gap_percent']:.2f}%. "
            f"Simulating acquisition of this skill is "
            f"estimated to increase MatchESCO by "
            f"{skill_gap_explanation['improvement_esco_percent']:.2f} "
            f"percentage points. "
            f"Of this, "
            f"{skill_gap_explanation['direct_improvement_percent']:.2f} "
            f"percentage points come from direct coverage "
            f"and "
            f"{skill_gap_explanation['semantic_spillover_percent']:.2f} "
            f"percentage points come from semantic spillover."
        )

    career_path_summary = None

    if career_path_explanation is not None:
        explanation_type = (career_path_explanation.get("explanation_type"))

        if explanation_type == "career_transition":
            recommendations = (career_path_explanation.get("recommendations",[]))
            if recommendations:
                top_candidate = recommendations[0]

                career_path_summary = (
                    f"In Career Transition mode, "
                    f"structural occupation similarity is "
                    f"used to generate related candidates, "
                    f"while the final user-specific ranking "
                    f"is based on MatchESCO. "
                    f"The highest-ranked returned candidate "
                    f"is '{top_candidate['occupation_name']}' "
                    f"with MatchESCO "
                    f"{top_candidate['match_esco_percent']:.2f}%."
                )

                if (top_candidate.get("occupation_similarity_percent") is not None):
                    career_path_summary += (
                        f" Its structural occupation Jaccard similarity with the current occupation is "
                        f"{top_candidate['occupation_similarity_percent']:.2f}%."
                    )
            else:
                career_path_summary = (
                    "Career Transition mode was used, but no explained recommendations were available in the supplied explanation."
                )

        elif explanation_type == "career_discovery":
            recommendations = (career_path_explanation.get("recommendations",[]))

            if recommendations:
                top_candidate = recommendations[0]

                career_path_summary = (
                    f"In Career Discovery mode, occupations "
                    f"are evaluated directly against the "
                    f"user's skill profile and ranked by "
                    f"MatchESCO. "
                    f"The highest-ranked returned occupation "
                    f"is '{top_candidate['occupation_name']}' "
                    f"with MatchESCO "
                    f"{top_candidate['match_esco_percent']:.2f}%."
                )
            else:
                career_path_summary = (
                    "Career Discovery mode was used, but no explained recommendations were available in the supplied explanation."
                )

        elif explanation_type == "career_skill_roadmap":
            career_path_summary = (
                f"The Personalized Career Skill Roadmap contains "
                f"{career_path_explanation['roadmap_step_count']} "
                f"sequential learning steps. Across the simulated roadmap, MatchESCO increases from "
                f"{career_path_explanation['initial_match_esco_percent']:.2f}% to "
                f"{career_path_explanation['final_match_esco_percent']:.2f}%, "
                f"corresponding to a total simulated increase of "
                f"{career_path_explanation['total_improvement_esco_percent']:.2f} "
                f"percentage points. The roadmap uses sequential recalculated marginal ImprovementESCO rather than a static initial ranking."
            )

        elif explanation_type == "career_path_comparison":
            career_path_summary = (career_path_explanation["explanation_text"])
        else:
            raise ValueError("Unsupported career_path explanation_type: "
                f"{explanation_type}"
            )

    graph_summary = None

    if graph_explanation is not None:
        explanation_type = (graph_explanation.get("explanation_type"))

        if explanation_type == "skill_graph":
            related_skills = (graph_explanation.get("related_skills", []))

            if related_skills:
                top_related = related_skills[0]

                graph_summary = (
                    f"Graph-based structural evidence shows "
                    f"that '{graph_explanation['skill_name']}' "
                    f"is most closely related among the "
                    f"returned skills to "
                    f"'{top_related['skill_name']}'. "
                    f"They share "
                    f"{top_related['shared_occupation_count']} "
                    f"occupation neighbors out of "
                    f"{top_related['union_occupation_count']} "
                    f"distinct occupations, producing a "
                    f"Jaccard similarity of "
                    f"{top_related['jaccard_percent']:.2f}%. "
                    f"This graph signal represents structural "
                    f"relatedness, not learning order or "
                    f"causal complementarity."
                )
            else:
                graph_summary = (
                    f"No related skills were returned for "
                    f"'{graph_explanation['skill_name']}' "
                    f"under the current graph criterion."
                )

        elif explanation_type == "occupation_graph":
            similar_occupations = (graph_explanation.get("similar_occupations", []))

            if similar_occupations:
                top_related = similar_occupations[0]

                graph_summary = (
                    f"Graph-based occupation analysis shows that "
                    f"'{top_related['occupation_name']}' "
                    f"is the highest-ranked structurally related occupation among the returned "
                    f"results for "
                    f"'{graph_explanation['current_occupation_name']}'. "
                    f"The two occupations share "
                    f"{top_related['shared_skill_count']} "
                    f"canonical ESCO skills out of "
                    f"{top_related['union_skill_count']} "
                    f"distinct skills, producing a Jaccard "
                    f"similarity of "
                    f"{top_related['jaccard_percent']:.2f}%."
                )
            else:
                graph_summary = (
                    f"No structurally related occupations were returned for "
                    f"'{graph_explanation['current_occupation_name']}'."
                )
        else:
            raise ValueError("Unsupported graph explanation_type: "
                f"{explanation_type}"
            )

    sections = []

    if job_match_summary is not None:
        sections.append(job_match_summary)

    if skill_gap_summary is not None:
        sections.append(skill_gap_summary)

    if career_path_summary is not None:
        sections.append(career_path_summary)

    if graph_summary is not None:
        sections.append(graph_summary)

    methodology_summary = (
        "The overall recommendation is therefore explained through separate evidence sources rather than a "
        "single combined score. MatchESCO represents canonical skill coverage, MatchMarket is used only "
        "as supplementary labor-market evidence, graph similarity represents structural relatedness, and "
        "learning priorities are determined by simulated ImprovementESCO."
    )

    sections.append(methodology_summary)
    overall_text = " ".join(sections)

    return {
        "explanation_type": "overall",
        "included_sections": list(provided_explanations.keys()),
        "job_match_summary": job_match_summary,
        "skill_gap_summary": skill_gap_summary,
        "career_path_summary": career_path_summary,
        "graph_summary": graph_summary, 
        "methodology_summary": methodology_summary,
        "explanation_text": overall_text
    }