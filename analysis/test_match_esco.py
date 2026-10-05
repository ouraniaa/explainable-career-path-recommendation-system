import sys
from pathlib import Path

#Allows importing from src/
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))

from src.match_esco import calculate_match_esco

#Temporary test occupation:Data Scientist
TARGET_OCCUPATION_ID = "258e46f9-0075-4a2e-adae-1ff0477e0f30"


#Temporary test user skills.
#Replace these IDs with real skill IDs from Neo4j.
USER_SKILL_IDS = [
    "5f0082ab-2131-49b5-94d6-a1821daf57d6",
    "505e4ef3-7ce4-437d-b7b4-5c608f71c258",
    "25f0ea33-b4a2-4f31-b7b4-7d20e827b180"
]


result = calculate_match_esco(TARGET_OCCUPATION_ID, USER_SKILL_IDS)

print("=" * 80)
print("MATCH ESCO TEST")
print("=" * 80)

print("Canonical ESCO skills:", result["canonical_skill_count"])
print("Exact matches:", result["exact_match_count"])
print("Semantic matches:", result["semantic_match_count"])
print("Total covered skills:", result["covered_skill_count"])

if result["match_esco"] is not None:
    print(
        "MatchESCO:",
        f"{result['match_esco'] * 100:.2f}%"
    )
else:
    print("MatchESCO: N/A")

print("\n" + "=" * 80)
print("SEMANTIC MATCHES")
print("=" * 80)

for detail in result["details"]:
    if detail["match_type"] == "semantic":
        print(f"Required: {detail['required_skill_name']}")
        print(f"Matched with: {detail['best_user_skill_name']}")
        print(f"Similarity: {detail['raw_similarity']}")
        print(f"Coverage: {detail['coverage']}")
        print("-" * 80)