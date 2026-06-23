"""
DSA Pattern Miner FastAPI backend.

Install:
    pip install fastapi uvicorn sqlalchemy psycopg2-binary pydantic

Run from this folder:
    set DATABASE_URL=postgresql+psycopg2://postgres:postgres@localhost:5432/dsa_pattern_miner
    uvicorn main:app --reload

Docs:
    http://127.0.0.1:8000/docs
"""

import os
from typing import Generator, Literal, Optional

from fastapi import Depends, FastAPI, HTTPException, Path, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker


DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg2://postgres:postgres@localhost:5432/dsa_pattern_miner",
)

engine: Engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

app = FastAPI(
    title="DSA Pattern Miner API",
    version="1.0.0",
    description="Backend API for company-wise DSA question and pattern insights.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


class Company(BaseModel):
    company_id: int
    company_name: str


class PatternInsight(BaseModel):
    pattern_name: str
    total_frequency: float = Field(..., description="Sum of frequencies for this company and pattern.")
    problem_count: int = Field(..., description="Number of distinct problems tagged with this pattern.")
    avg_frequency: float = Field(..., description="Average frequency across matching problems.")


class RoadmapProblem(BaseModel):
    rank: int
    title: str
    leetcode_id: Optional[int] = None
    difficulty: Optional[Literal["Easy", "Medium", "Hard"]] = None
    acceptance_rate: Optional[float] = None
    url: Optional[str] = None
    patterns: list[str] = Field(default_factory=list)
    frequency_count: float
    importance_score: float
    timeframe: str


class RoadmapResponse(BaseModel):
    company_name: str
    days_to_prep: int
    daily_target: int
    total_questions: int
    questions: list[RoadmapProblem]


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def ensure_company_exists(db: Session, company_name: str) -> None:
    exists = db.execute(
        text(
            """
            SELECT 1
            FROM companies
            WHERE lower(company_name) = lower(:company_name)
            LIMIT 1
            """
        ),
        {"company_name": company_name},
    ).scalar()
    if not exists:
        raise HTTPException(status_code=404, detail=f"Company not found: {company_name}")


@app.get("/health")
def health_check(db: Session = Depends(get_db)) -> dict[str, str]:
    db.execute(text("SELECT 1"))
    return {"status": "ok"}


@app.get("/companies/", response_model=list[Company])
def list_companies(db: Session = Depends(get_db)) -> list[Company]:
    rows = db.execute(
        text(
            """
            SELECT company_id, company_name
            FROM companies
            ORDER BY company_name ASC
            """
        )
    ).mappings()
    return [Company(**row) for row in rows]


@app.get("/companies/{company_name}/top-patterns", response_model=list[PatternInsight])
def get_top_patterns(
    company_name: str = Path(..., min_length=1),
    limit: int = Query(default=10, ge=1, le=100),
    timeframe: Optional[str] = Query(default=None, description="Optional timeframe such as all_time or six_months."),
    db: Session = Depends(get_db),
) -> list[PatternInsight]:
    ensure_company_exists(db, company_name)

    rows = db.execute(
        text(
            """
            SELECT
                pat.pattern_name,
                COALESCE(SUM(cpf.frequency_count), 0)::float AS total_frequency,
                COUNT(DISTINCT p.problem_id)::int AS problem_count,
                COALESCE(AVG(cpf.frequency_count), 0)::float AS avg_frequency
            FROM companies c
            JOIN company_problem_frequencies cpf ON cpf.company_id = c.company_id
            JOIN problems p ON p.problem_id = cpf.problem_id
            JOIN problem_patterns pp ON pp.problem_id = p.problem_id
            JOIN patterns pat ON pat.pattern_id = pp.pattern_id
            WHERE lower(c.company_name) = lower(:company_name)
              AND (:timeframe IS NULL OR cpf.timeframe = :timeframe)
            GROUP BY pat.pattern_name
            ORDER BY total_frequency DESC, problem_count DESC, pat.pattern_name ASC
            LIMIT :limit
            """
        ),
        {"company_name": company_name, "timeframe": timeframe, "limit": limit},
    ).mappings()

    return [PatternInsight(**row) for row in rows]


@app.get("/roadmap/generate", response_model=RoadmapResponse)
def generate_roadmap(
    company_name: str = Query(..., min_length=1),
    days_to_prep: int = Query(..., ge=1, le=365),
    daily_target: int = Query(default=5, ge=1, le=20),
    timeframe: Optional[str] = Query(default=None, description="Optional timeframe such as all_time or six_months."),
    db: Session = Depends(get_db),
) -> RoadmapResponse:
    ensure_company_exists(db, company_name)

    max_questions = days_to_prep * daily_target
    rows = db.execute(
        text(
            """
            WITH ranked_company_problems AS (
                SELECT
                    c.company_name,
                    p.problem_id,
                    p.title,
                    p.leetcode_id,
                    p.difficulty,
                    p.acceptance_rate::float AS acceptance_rate,
                    p.url,
                    cpf.timeframe,
                    cpf.frequency_count::float AS frequency_count,
                    CASE p.difficulty
                        WHEN 'Hard' THEN 1.30
                        WHEN 'Medium' THEN 1.10
                        WHEN 'Easy' THEN 0.90
                        ELSE 1.00
                    END AS difficulty_weight,
                    ROW_NUMBER() OVER (
                        PARTITION BY p.problem_id
                        ORDER BY
                            CASE cpf.timeframe
                                WHEN 'six_months' THEN 5
                                WHEN 'thirty_days' THEN 4
                                WHEN 'three_months' THEN 3
                                WHEN 'one_year' THEN 2
                                WHEN 'all_time' THEN 1
                                ELSE 0
                            END DESC,
                            cpf.frequency_count DESC
                    ) AS problem_row_rank
                FROM companies c
                JOIN company_problem_frequencies cpf ON cpf.company_id = c.company_id
                JOIN problems p ON p.problem_id = cpf.problem_id
                WHERE lower(c.company_name) = lower(:company_name)
                  AND (:timeframe IS NULL OR cpf.timeframe = :timeframe)
            ),
            pattern_rollup AS (
                SELECT
                    pp.problem_id,
                    ARRAY_AGG(DISTINCT pat.pattern_name ORDER BY pat.pattern_name) AS patterns
                FROM problem_patterns pp
                JOIN patterns pat ON pat.pattern_id = pp.pattern_id
                GROUP BY pp.problem_id
            )
            SELECT
                r.title,
                r.leetcode_id,
                r.difficulty,
                r.acceptance_rate,
                r.url,
                COALESCE(pr.patterns, ARRAY[]::text[]) AS patterns,
                r.frequency_count,
                ROUND((r.frequency_count * r.difficulty_weight)::numeric, 2)::float AS importance_score,
                r.timeframe
            FROM ranked_company_problems r
            LEFT JOIN pattern_rollup pr ON pr.problem_id = r.problem_id
            WHERE r.problem_row_rank = 1
            ORDER BY importance_score DESC, r.frequency_count DESC, r.title ASC
            LIMIT :max_questions
            """
        ),
        {
            "company_name": company_name,
            "timeframe": timeframe,
            "max_questions": max_questions,
        },
    ).mappings()

    questions = [
        RoadmapProblem(rank=index, **row)
        for index, row in enumerate(rows, start=1)
    ]

    canonical_company_name = db.execute(
        text(
            """
            SELECT company_name
            FROM companies
            WHERE lower(company_name) = lower(:company_name)
            LIMIT 1
            """
        ),
        {"company_name": company_name},
    ).scalar_one()

    return RoadmapResponse(
        company_name=canonical_company_name,
        days_to_prep=days_to_prep,
        daily_target=daily_target,
        total_questions=len(questions),
        questions=questions,
    )
