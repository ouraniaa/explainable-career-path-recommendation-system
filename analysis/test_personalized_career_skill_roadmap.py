import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.personalized_career_skill_roadmap import (generate_personalized_career_skill_roadmap)
from src.learning_priority import (calculate_learning_priority)

TARGET_OCCUPATION_ID = ("258e46f9-0075-4a2e-adae-1ff0477e0f30")

USER_SKILL_IDS = [
    "5f0082ab-2131-49b5-94d6-a1821daf57d6",
    "505e4ef3-7ce4-437d-b7b4-5c608f71c258",
    "25f0ea33-b4a2-4f31-b7b4-7d20e827b180"
]

#1. INITIAL SINGLE-STEP RANKING
initial_priority = calculate_learning_priority(
    occupation_id=TARGET_OCCUPATION_ID,
    user_skill_ids=USER_SKILL_IDS,
    top_n=5
)

initial_top_5 = initial_priority["ranked_skills"]

initial_top_skill = initial_top_5[0]

#2. GENERATE ROADMAP
roadmap = generate_personalized_career_skill_roadmap(
    occupation_id=TARGET_OCCUPATION_ID,
    user_skill_ids=USER_SKILL_IDS,
    max_steps=5
)

steps = roadmap["roadmap_steps"]

print("=" * 80)
print("PERSONALIZED CAREER SKILL ROADMAP TEST")
print("=" * 80)

print("Selection method:", roadmap["selection_method"])

print("Selection strategy:", roadmap["selection_strategy"])
print(
    "Initial MatchESCO:",
    f"{roadmap['initial_match_esco'] * 100:.4f}%"
)
print(
    "Final MatchESCO:",
    f"{roadmap['final_match_esco'] * 100:.4f}%"
)
print("Roadmap steps:", roadmap["roadmap_step_count"])
print("Remaining candidate skills:", roadmap["remaining_candidate_skill_count"])

assert (roadmap["selection_method"] == "sequential_marginal_improvement_esco")
assert (roadmap["selection_strategy"] == "greedy")
assert roadmap["roadmap_step_count"] <= 5
assert roadmap["roadmap_step_count"] > 0
assert len(steps) == roadmap["roadmap_step_count"]
assert (roadmap["final_match_esco"] >= roadmap["initial_match_esco"])

#5. FIRST STEP MUST MATCH INITIAL TOP RECOMMENDATION
first_step = steps[0]

assert (first_step["skill_id"] == initial_top_skill["skill_id"])
assert (first_step["skill_name"] == initial_top_skill["skill_name"])

assert abs(
    first_step["marginal_improvement_esco"]
    - initial_top_skill["improvement_esco"]
) < 1e-10

#6. VERIFY EACH ROADMAP STEP
previous_match_esco = roadmap["initial_match_esco"]

selected_skill_ids = set()

for expected_step_number, step in enumerate(steps, start=1):
    assert (step["step"] == expected_step_number)
    assert step["skill_id"]
    assert step["skill_name"]

    #No skill should be selected twice.
    assert (step["skill_id"] not in selected_skill_ids)

    selected_skill_ids.add(step["skill_id"])

    #Match before should equal previous step's state.
    assert abs(step["match_esco_before"] - previous_match_esco) < 1e-10

    #Match should never decrease.
    assert (step["match_esco_after"] >= step["match_esco_before"])

    #Marginal improvement should equal full score delta.
    actual_delta = (step["match_esco_after"] - step["match_esco_before"])

    assert abs(
        actual_delta
        - step["marginal_improvement_esco"]
    ) < 1e-10

    assert (step["marginal_improvement_esco"] >= 0.0)

    assert (step["direct_improvement"] >= 0.0)
    assert (step["semantic_spillover"] >= 0.0)
    assert (0.0 <= step["semantic_dependency_ratio"] <= 1.0)

    previous_match_esco = (step["match_esco_after"])


#Final score must equal last step's after score.
assert abs(roadmap["final_match_esco"] - steps[-1]["match_esco_after"]) < 1e-10


print("\nPERSONALIZED CAREER SKILL ROADMAP TEST PASSED")

#7. DISPLAY INITIAL RANKING
print("\n" + "=" * 80)
print("INITIAL LEARNING PRIORITY TOP 5")
print("=" * 80)

for item in initial_top_5:
    print(
        f"Rank {item['rank']}: "
        f"{item['skill_name']}"
    )

    print(
        "  ImprovementESCO:",
        f"{item['improvement_esco'] * 100:.4f} "
        "percentage points"
    )


#8. DISPLAY SEQUENTIAL ROADMAP
print("\n" + "=" * 80)
print("SEQUENTIAL ROADMAP")
print("=" * 80)

for step in steps:
    print(
        f"Step {step['step']}: "
        f"{step['skill_name']}"
    )
    print(
        "  ESCO relation:",
        step["relation_type"]
    )
    print(
        "  MatchESCO before:",
        f"{step['match_esco_before'] * 100:.4f}%"
    )
    print(
        "  MatchESCO after:",
        f"{step['match_esco_after'] * 100:.4f}%"
    )
    print(
        "  Marginal ImprovementESCO:",
        f"{step['marginal_improvement_esco'] * 100:.4f} "
        "percentage points"
    )
    print(
        "  Direct Improvement:",
        f"{step['direct_improvement'] * 100:.4f} "
        "percentage points"
    )
    print(
        "  Semantic Spillover:",
        f"{step['semantic_spillover'] * 100:.4f} "
        "percentage points"
    )
    print(
        "  Semantic Dependency Ratio:",
        f"{step['semantic_dependency_ratio']:.4f}"
    )

    if step["marginal_improvement_market"] is not None:
        print(
            "  Market Improvement:",
            f"{step['marginal_improvement_market'] * 100:.4f} "
            "percentage points"
        )
    else:
        print(
            "  Market Improvement: N/A"
        )
    print(
        "  Affected ESCO skills:",
        step["affected_esco_skill_count"]
    )
    print(
        "  Selection reason:",
        step["selection_reason"]
    )
    print("-" * 80)

#9. CHECK WHETHER ROADMAP DIFFERS FROM STATIC TOP-5
initial_top_5_ids = [
    item["skill_id"]
    for item in initial_top_5
]

roadmap_ids = [
    step["skill_id"]
    for step in steps
]

print("\n" + "=" * 80)
print("STATIC VS SEQUENTIAL COMPARISON")
print("=" * 80)

print("Initial top-5 skill names:")

for item in initial_top_5:
    print(" -", item["skill_name"])

print("\nSequential roadmap skill names:")

for step in steps:
    print(" -", step["skill_name"])

if roadmap_ids == initial_top_5_ids[:len(roadmap_ids)]:
    print("\nThe sequential roadmap currently matches the initial static ranking for these steps."
    )

else:
    print("\nThe sequential roadmap differs from the initial static ranking after recalculation.")
    print("This confirms that marginal improvements changed after simulated skill acquisition.")