"""
Defines the FastAPI layer of the Career Recommendation system.

This file starts and closes the Neo4j connection, configures the API, 
validating incoming request data, and exposes the main endpoints used
by the frontend.

The API receives the request, calls the appropriate functions from the 
recommendation layer, and returns their results to the frontend.
"""
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from neo4j import GraphDatabase
from neo4j.exceptions import Neo4jError
from pydantic import BaseModel, Field
from dotenv import load_dotenv

from src.application_service import (analyze_career_paths, analyze_target_occupation)
from src.career_transition_recommendation import (get_discovery_candidate_occupations)

load_dotenv()

NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")

if not NEO4J_PASSWORD:
    raise RuntimeError("NEO4J_PASSWORD environment variable is required.")

driver = None

#Application Lifespan
@asynccontextmanager
async def lifespan(app: FastAPI):
    global driver

    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

    try:
        driver.verify_connectivity()
        yield

    finally:
        if driver is not None:
            driver.close()


#FastAPI app
app = FastAPI(title="Career Recommendation API", version="1.0.0", lifespan=lifespan)

#CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


#Request models
class TargetOccupationRequest(BaseModel):
    occupation_id: str
    occupation_name: str
    user_skill_ids: list[str] = Field(min_length=1)
    learning_priority_top_n: int = Field(default=5, ge=1)
    graph_top_n: int = Field(default=3, ge=1)
    roadmap_max_steps: int = Field(default=5, ge=1)

class CareerPathsRequest(BaseModel):
    user_skill_ids: list[str] = Field(min_length=1)
    current_occupation_id: (str | None) = None
    structural_top_n: int = Field(default=10, ge=1)
    recommendation_top_n: int = Field(default=5, ge=1)
    min_shared_skills: int = Field(default=1, ge=1)


@app.get("/")
def root():
    return {
        "message": "Career Recommendation API is running."
    }


@app.get("/health")
def health():
    return {
        "status": "ok"
    }

@app.get("/api/skills")
def search_skills(q: str = Query(default="", min_length=0), limit: int = Query(default=20, ge=1, le=50)):
    """
    Searches ESCO skills by name.

    Ranking priority:
    1. exact match
    2. skill name starts with the search query
    3. one of the skill-name words starts with the search query
    """
    try:
        search_text = q.strip().lower()

        if len(search_text) < 2:
            return {
                "query": q,
                "count": 0,
                "skills": []
            }

        with driver.session() as session:
            query = """
            MATCH (s:Skill)

            WHERE
                s.name IS NOT NULL
                AND toLower(s.name) CONTAINS $search

            WITH
                s,
                CASE
                    WHEN toLower(s.name) = $search
                    THEN 0

                    WHEN toLower(s.name) STARTS WITH $search
                    THEN 1

                    ELSE 2
                END AS search_rank

            RETURN DISTINCT
                s.esco_id AS skill_id,
                s.name AS skill_name,
                search_rank

            ORDER BY
                search_rank ASC,
                size(skill_name) ASC,
                toLower(skill_name) ASC

            LIMIT $limit
            """

            records = session.run(query, search=search_text, limit=limit)

            skills = [
                {
                    "skill_id": record["skill_id"],
                    "skill_name": record["skill_name"]
                }
                for record in records
            ]

        return {
            "query": q,
            "count": len(skills),
            "skills": skills
        }

    except Neo4jError:
        raise HTTPException(status_code=503, detail="Neo4j database operation failed.")
    
@app.post("/api/analyze-target-occupation")
def analyze_target_occupation_endpoint(request: TargetOccupationRequest):
    try:
        with driver.session() as session:
            result = (analyze_target_occupation(session=session, 
                    occupation_id=(request.occupation_id),
                    occupation_name=(request.occupation_name),
                    user_skill_ids=(request.user_skill_ids),
                    learning_priority_top_n=(request.learning_priority_top_n),
                    graph_top_n=(request.graph_top_n),
                    roadmap_max_steps=(request.roadmap_max_steps),
                )
            )

        return result

    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    except Neo4jError:
        raise HTTPException(status_code=503, detail=("Neo4j database operation failed."))

    except Exception as exc:
        raise HTTPException(status_code=500, detail=("An unexpected server error occurred."))


@app.post("/api/analyze-career-paths")
def analyze_career_paths_endpoint(request: CareerPathsRequest):
    try:
        with driver.session() as session:
            result = (analyze_career_paths(
                    session=session,
                    user_skill_ids=(request.user_skill_ids),
                    current_occupation_id=(request.current_occupation_id),
                    structural_top_n=(request.structural_top_n),
                    recommendation_top_n=(request.recommendation_top_n),
                    min_shared_skills=(request.min_shared_skills)
                )
            )

        return result

    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    except Neo4jError:
        raise HTTPException(status_code=503, detail=("Neo4j database operation failed."))

    except Exception as exc:
        raise HTTPException(status_code=500, detail=("An unexpected server error occurred."))


@app.get("/api/occupations")
def search_occupations(q: str = Query(default=""), limit: int = Query(default=20, ge=1, le=50)):
    """
    Searches occupations available in the analytical occupation profile.
    """
    try:
        occupations = (get_discovery_candidate_occupations())
        search_text = (q.strip().lower())

        if search_text:
            filtered = []
            for occupation in occupations:
                name = (occupation["occupation_name"] or "")
                normalized_name = (name.lower())
                if (search_text not in normalized_name):
                    continue
                if (normalized_name == search_text):
                    search_rank = 0
                elif (normalized_name.startswith(search_text)):
                    search_rank = 1
                else:
                    search_rank = 2
                filtered.append((search_rank,len(name), normalized_name, occupation))
            filtered.sort(
                key=lambda item: (
                    item[0],
                    item[1],
                    item[2],
                )
            )

            occupations = [item[3]
                for item in filtered
            ]
        else:
            occupations = sorted(
                occupations,
                key=lambda occupation: (
                    occupation["occupation_name"].lower()
                )
            )

        occupations = (occupations[:limit])

        return {
            "query": q,
            "count": len(occupations),
            "occupations": occupations
        }

    except Exception as exc:
        raise HTTPException(status_code=500, detail=("Could not load occupations."))

@app.get("/api/current-occupations")
def search_current_occupations(q: str = Query(default=""), limit: int = Query(default=20, ge=1, le=50)):
    """
    Searches occupations directly from the Knowledge Graph.
    """
    try:
        search_text = q.strip()
        with driver.session() as session:
            query = """
            MATCH (o:Occupation)

            WHERE
                o.name IS NOT NULL
                AND (
                    $search = ""
                    OR toLower(o.name)
                       CONTAINS toLower($search)
                )

            WITH
                o,
                CASE
                    WHEN toLower(o.name) =
                         toLower($search)
                    THEN 0

                    WHEN toLower(o.name)
                         STARTS WITH
                         toLower($search)
                    THEN 1

                    ELSE 2
                END AS search_rank

            RETURN DISTINCT
                o.esco_id AS occupation_id,
                o.name AS occupation_name,
                o.isco_group AS isco_group,
                search_rank

            ORDER BY
                search_rank ASC,
                size(occupation_name) ASC,
                toLower(occupation_name) ASC

            LIMIT $limit
            """

            records = session.run(query, search=search_text, limit=limit)
            occupations = [
                {
                    "occupation_id": record["occupation_id"],
                    "occupation_name": record["occupation_name"],
                    "isco_group": record["isco_group"],
                }
                for record in records
            ]

        return {
            "query": q,
            "count": len(occupations),
            "occupations": occupations
        }
 
    except Neo4jError:
        raise HTTPException(status_code=503, detail=("Neo4j database operation failed."))