# Explainable Career Path Recommendation System

This project was developed as part of an undergraduate thesis and implements an explainable career recommendation system using Knowledge Graphs, ESCO occupational data, labor-market evidence, semantic similarity, and graph-based methods.

The system supports:
- Target Occupation Analysis
- Career Transition Recommendations
- Career Discovery Recommendations
- Skill Gap Analysis
- Personalized Skill Recommendations
- Personalized Career Skill Roadmap

## Technologies

- **Backend:** Python, FastAPI, Pandas, NumPy, Sentence Transformers
- **Database:** Neo4j (Graph Database)
- **Frontend:** React, TypeScript, Vite

---

## Project Structure
```text
Thesis_project/
├── api/                  # FastAPI backend
├── data/                 # Raw, processed, and evaluation data
├── experiments/          # Experimental scripts and notebooks
│   └── build_knowledge_graph.ipynb
├── frontend/             # React frontend
├── src/                  # Core recommendation and explainability logic
├── analysis/             # Integration, validation, and diagnostic scripts
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md

Knowledge Graph
The Neo4j graph contains the main entities: JobPosting, Occupation, and Skill.

Main relationships:
(:JobPosting)-[:REQUIRES]->(:Skill)
(:JobPosting)-[:BELONGS_TO]->(:Occupation)
(:Occupation)-[:ESCO_REQUIRES]->(:Skill)

Note: ESCO is used as the canonical source for occupation-skill requirements, while job-posting data is used as supplementary labor-market evidence.

Recommendation Methodology
MatchESCO
MatchESCO measures user coverage of the canonical ESCO skills required by an occupation.

Exact ESCO skill matches receive full coverage.

For non-exact matches, semantic similarity is calculated using sentence-transformers/all-mpnet-base-v2.

Semantic similarity is used to provide partial coverage for sufficiently related skills.

MatchMarket
MatchMarket provides supplementary labor-market evidence using occupation-specific RCA (Revealed Comparative Advantage) values. It is kept separate from MatchESCO and is not combined into a single recommendation score.

Skill Gap Analysis
Skill gaps are calculated over the canonical ESCO skill requirements of an occupation. For each required skill: gap = 1 - coverage. Skills with no meaningful coverage are treated as missing skills.

Learning Priority
Missing skills are evaluated by simulating their addition to the user profile and recalculating MatchESCO. Skills are ranked according to their expected improvement in MatchESCO.

Graph-Based Similarity
Unweighted Jaccard similarity is used to measure structural similarity between:

Occupations based on shared canonical ESCO skills.

Skills based on shared ESCO occupation neighborhoods.

Structural similarity is used for candidate generation and explanation, not as a replacement for semantic similarity.

Career Transition & Discovery
Career Transition: Follows a two-stage process:

Generate structurally similar occupation candidates using Jaccard similarity.

Rank those candidates according to the user's MatchESCO score.

Career Discovery: Evaluates the analytical occupation set directly using MatchESCO when the user does not provide a current occupation.

Personalized Career Skill Roadmap
The roadmap follows a greedy sequential strategy. At each step, the system selects the skill with the highest current MatchESCO improvement, adds it to the simulated user profile, and recalculates the remaining priorities.

Explainability
The system provides deterministic explanations based on already calculated recommendation results. The explainability layer does not introduce additional scoring logic. Explanations are provided for: occupation matching, skill gaps, graph similarity, career transitions, career discovery, personalized skill recommendations, and the career skill roadmap.

Setup
1. Install Python dependencies
From the project root:

Bash
pip install -r requirements.txt
2. Configure environment variables
Create a .env file in the project root based on .env.example. Do not commit the .env file.

Code snippet
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=<your-password>
3. Run the backend
From the project root:

Bash
python -m uvicorn api.main:app --reload --port 8001
The FastAPI documentation will be available at: http://127.0.0.1:8001/docs

4. Run the frontend
Open a second terminal:

Bash
cd frontend
npm install
npm run dev
The frontend will be available at: http://localhost:5173/

Data Preparation
The project includes scripts for importing ESCO data, cleaning and deduplicating job postings, constructing occupation-skill profiles, calculating RCA values, and generating semantic skill embeddings.

The original graph construction workflow is preserved in experiments/build_knowledge_graph.ipynb. This notebook documents the initial preparation of Skillab job-posting data, parsing of ESCO skill identifiers, creation of the initial JobPosting-Skill graph, and enrichment of Skill nodes with official ESCO labels.

Limitations & Notes
ESCO is treated as the canonical occupational skill taxonomy.

Job-posting evidence is supplementary and may contain dataset-specific noise or bias.

MatchESCO represents skill coverage and should not be interpreted as an employability probability.

Semantic similarity and structural graph similarity represent different types of evidence.

The personalized career skill roadmap is greedy and sequential. It should be interpreted as a suggested learning path rather than a globally optimal plan.

Thesis
This repository accompanies the undergraduate thesis: Development of an Explainable Career Path Recommendation System using Knowledge Graphs and Graph Algorithms.