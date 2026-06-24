# 🚀 LeetSight API

The backend engine for the LeetSight ecosystem. This FastAPI-powered server manages a massive dataset of 18,000+ coding interview questions, implements an AI-driven pattern auto-tagger, and serves high-concurrency analytics to the frontend.

## 🛠️ Architecture & Tech Stack
* **Framework:** FastAPI (High-performance asynchronous processing)
* **Database:** PostgreSQL (SQLAlchemy ORM)
* **Intelligence:** Custom Python scripts for data ingestion and ML-based pattern auto-tagging.
* **Infrastructure:** Render (Web Service & Cloud PostgreSQL)

## 📡 Core Endpoints
| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/companies` | Returns a list of all indexed companies. |
| `GET` | `/companies/{company}/top-patterns` | Fetches aggregated DSA frequency data for a target company. |
| `GET` | `/roadmap/generate` | Generates a prioritized study sequence using custom pathfinding logic. |

## ⚙️ Backend Pipelines
This API includes custom management scripts to maintain data integrity:
* **`ingest_dsa_patterns.py`**: Automated ingestion pipeline for batch processing thousands of CSV records.
* **`auto_tagger.py`**: Machine learning script that analyzes problem semantics to auto-assign missing DSA tags.

## 🚀 Deployment
Deployed on Render with secure CORS configurations to handle cross-origin requests from the Vercel-hosted frontend.

---
*High-performance data delivery for technical interview mastery.*
