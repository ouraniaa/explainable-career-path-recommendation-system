import sys
import os
from pathlib import Path
from dotenv import load_dotenv
from neo4j import GraphDatabase

PROJECT_ROOT = Path(__file__).resolve().parents[2]

sys.path.insert(0, str(PROJECT_ROOT))

from src.career_transition_recommendation import (generate_career_transition_recommendations, generate_career_discovery_recommendations)
from src.personalized_career_skill_roadmap import (generate_personalized_career_skill_roadmap)
from src.explainability.career_path_explanation import (
    generate_career_transition_explanation,
    generate_career_discovery_explanation,
    generate_career_path_comparison_explanation,
    generate_career_skill_roadmap_explanation
)

load_dotenv

NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USER = os.getenv("NEO4J_USER")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")

if not NEO4J_URI or not NEO4J_USER or not NEO4J_PASSWORD:
    raise RuntimeError("Neo4j environment variables are required.")

CURRENT_OCCUPATION_ID = ("258e46f9-0075-4a2e-adae-1ff0477e0f30")
TARGET_OCCUPATION_ID = ("258e46f9-0075-4a2e-adae-1ff0477e0f30")
USER_SKILL_IDS = [
    "5f0082ab-2131-49b5-94d6-a1821daf57d6",
    "505e4ef3-7ce4-437d-b7b4-5c608f71c258",
    "25f0ea33-b4a2-4f31-b7b4-7d20e827b180"
]

driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

with driver.session() as session:
    transition_result = (generate_career_transition_recommendations(
            session=session,
            current_occupation_id=CURRENT_OCCUPATION_ID,
            user_skill_ids=USER_SKILL_IDS,
            structural_top_n=10,
            recommendation_top_n=5,
            min_shared_skills=1
        )
    )

    transition_explanation = (generate_career_transition_explanation(transition_result))

    assert (transition_explanation["explanation_type"] == "career_transition")
    assert (transition_explanation["current_occupation_id"] == CURRENT_OCCUPATION_ID)
    assert (transition_explanation["ranking_criterion"] == "match_esco")
    assert (transition_explanation["general_explanation"])
    assert (len(transition_explanation["recommendations"]) == len(transition_result["recommendations"]))

    for original, explained in zip(transition_result["recommendations"], transition_explanation["recommendations"]):
        assert (explained["occupation_id"] == original["occupation_id"])
        assert (explained["occupation_name"] == original["occupation_name"])
        assert (explained["structural_rank"] == original["structural_rank"])
        assert abs(explained["occupation_similarity"] - original["occupation_similarity"]) < 1e-12
        assert abs(explained["match_esco"] - original["match_esco"]) < 1e-12
        assert (explained["shared_skill_count"] == original["shared_skill_count"])
        assert (explained["union_skill_count"] == original["union_skill_count"])
        assert (explained["explanation_text"])

    discovery_result = (generate_career_discovery_recommendations(user_skill_ids=USER_SKILL_IDS, recommendation_top_n=5))

    discovery_explanation = (generate_career_discovery_explanation(discovery_result))

    assert (discovery_explanation["explanation_type"] == "career_discovery")
    assert (discovery_explanation["ranking_criterion"] == "match_esco")
    assert (discovery_explanation["candidate_count"] == discovery_result["candidate_count"])
    assert (discovery_explanation["general_explanation"])
    assert (len(discovery_explanation["recommendations"]) == len(discovery_result["recommendations"]))

    for original, explained in zip(discovery_result["recommendations"], discovery_explanation["recommendations"]):
        assert (explained["occupation_id"] == original["occupation_id"])
        assert (explained["occupation_name"] == original["occupation_name"])
        assert abs(explained["match_esco"] - original["match_esco"]) < 1e-12
        assert (explained["explanation_text"])

    transition_recommendations = (transition_result["recommendations"])

    assert (len(transition_recommendations) >= 2)

    preferred_candidate = (transition_recommendations[0])
    alternative_candidate = (transition_recommendations[-1])

    comparison_explanation = (generate_career_path_comparison_explanation(preferred_candidate=preferred_candidate, alternative_candidate=alternative_candidate))

    assert (comparison_explanation["explanation_type"] == "career_path_comparison")
    assert (comparison_explanation["preferred_occupation"] == preferred_candidate["occupation_name"])
    assert (comparison_explanation["alternative_occupation"] == alternative_candidate["occupation_name"])
    assert (comparison_explanation["preferred_match_esco"] >= comparison_explanation["alternative_match_esco"])

    expected_difference = (preferred_candidate["match_esco"] - alternative_candidate["match_esco"])

    assert abs(comparison_explanation["match_difference"] - expected_difference) < 1e-12
    assert (comparison_explanation["structural_comparison"] is not None)
    assert (comparison_explanation["explanation_text"])

    roadmap_result = (generate_personalized_career_skill_roadmap(occupation_id=TARGET_OCCUPATION_ID, user_skill_ids=USER_SKILL_IDS, max_steps=5))

    roadmap_explanation = (generate_career_skill_roadmap_explanation(roadmap_result))

    assert (roadmap_explanation["explanation_type"] == "career_skill_roadmap")
    assert (roadmap_explanation["occupation_id"] == TARGET_OCCUPATION_ID)
    assert (roadmap_explanation["selection_method"] == roadmap_result["selection_method"])
    assert (roadmap_explanation["selection_strategy"] == roadmap_result["selection_strategy"])
    assert (roadmap_explanation["roadmap_step_count"] == roadmap_result["roadmap_step_count"])
    assert abs(
        roadmap_explanation["initial_match_esco"] - roadmap_result["initial_match_esco"] 
    ) < 1e-12
    assert abs(
        roadmap_explanation["final_match_esco"] - roadmap_result["final_match_esco"]
    ) < 1e-12

    expected_total_improvement = (roadmap_result["final_match_esco"] - roadmap_result["initial_match_esco"])
    assert abs(
        roadmap_explanation["total_improvement_esco"] - expected_total_improvement
    ) < 1e-12
    assert (roadmap_explanation["remaining_candidate_skill_count"] == roadmap_result["remaining_candidate_skill_count"])
    assert (roadmap_explanation["general_explanation"])
    assert (roadmap_explanation["impact_explanation"])
    assert (roadmap_explanation["explanation_text"])

    assert (len(roadmap_explanation["roadmap_steps"]) == len(roadmap_result["roadmap_steps"]))

    for original, explained in zip(roadmap_result["roadmap_steps"], roadmap_explanation["roadmap_steps"]):
        assert (explained["step"] == original["step"])
        assert (explained["skill_id"] == original["skill_id"])
        assert (explained["skill_name"] == original["skill_name"])
        assert (explained["relation_type"] == original["relation_type"])
        assert abs(
            explained["match_esco_before"] - original["match_esco_before"]
        ) < 1e-12
        assert abs(
            explained["match_esco_after"] - original["match_esco_after"]
        ) < 1e-12
        assert abs(
            explained["marginal_improvement_esco"] - original["marginal_improvement_esco"]
        ) < 1e-12
        assert abs(
            explained["direct_improvement"] - original["direct_improvement"]
        ) < 1e-12
        assert abs(
            explained["semantic_spillover"] - original["semantic_spillover"]
        ) < 1e-12
        assert abs(
            explained["semantic_dependency_ratio"] - original["semantic_dependency_ratio"]
        ) < 1e-12

        assert (explained["affected_esco_skill_count"] == original["affected_esco_skill_count"])
        assert (explained["explanation_text"])

    print("=" * 80)
    print("CAREER TRANSITION EXPLANATION")
    print("=" * 80)

    print(transition_explanation["general_explanation"])

    print("\nTop career transition recommendations:\n")

    for item in transition_explanation["recommendations"]:
        print(
            f"Rank {item['rank']}: "
            f"{item['occupation_name']}"
        )

        print("  Structural rank:", item["structural_rank"])
        print("  Occupation Jaccard:", f"{item['occupation_similarity_percent']:.2f}%")
        print("  MatchESCO:", f"{item['match_esco_percent']:.2f}%")
        print("  Explanation:")
        print(" ", item["explanation_text"])
        print("-" * 80)

    print("\n" + "=" * 80)
    print("CAREER DISCOVERY EXPLANATION")
    print("=" * 80)

    print(discovery_explanation["general_explanation"])

    print("\nTop discovery recommendations:\n")

    for item in discovery_explanation["recommendations"]:
        print(
            f"Rank {item['rank']}: "
            f"{item['occupation_name']}"
        )
        print("  MatchESCO:", f"{item['match_esco_percent']:.2f}%")
        print("  Explanation:")
        print(" ", item["explanation_text"])
        print("-" * 80)
    print("\n" + "=" * 80)
    print("WHY NOT ANOTHER CAREER PATH?")
    print("=" * 80)
    print(comparison_explanation["explanation_text"])

    print("\n" + "=" * 80)
    print("PERSONALIZED CAREER SKILL ROADMAP EXPLANATION")
    print("=" * 80)
    print(roadmap_explanation["general_explanation"])
    print("\n", roadmap_explanation["impact_explanation"])
    print("\nRoadmap steps:\n")

    for step in roadmap_explanation["roadmap_steps"]:
        print(
            f"Step {step['step']}: "
            f"{step['skill_name']}"
        )
        print("  MatchESCO:", f"{step['match_esco_before_percent']:.2f}% ->"  
            f"{step['match_esco_after_percent']:.2f}%"
        )
        print("  ImprovementESCO:", f"{step['marginal_improvement_esco_percent']:.2f}, percentage points")
        print("  Semantic dependency:", f"{step['semantic_dependency_percent']:.2f}%")
        print("  Explanation:")
        print(" ", step["explanation_text"])
        print("-" * 80)


print("\n" + "=" * 80)
print("CAREER PATH EXPLANATION TEST PASSED")
print("=" * 80)

driver.close()