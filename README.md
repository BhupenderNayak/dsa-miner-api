# 🚀 DSA Miner API

**DSA Miner API** is the backend intelligence layer powering the **LeetSight Dashboard**. Built with **FastAPI** and **PostgreSQL**, it ingests, normalizes, and serves analytics over **18,000+ coding interview questions**, enabling company-wise DSA pattern insights, automated tagging, and roadmap generation at scale.

## 🌐 Frontend Companion

This API is consumed by the LeetSight frontend:

👉 https://github.com/BhupenderNayak/dsa-dashboard

---

## ✨ What This Service Does

- Serves company-wise interview analytics through a REST API
- Aggregates DSA pattern frequency across thousands of questions
- Generates prioritized study roadmaps from interview data
- Automates pattern tagging for unstructured question records
- Maintains strict validation and data integrity across the dataset
- Supports high-concurrency access with low-latency responses

---

## 🛠️ Architecture & Tech Stack

### Core Backend
- **FastAPI** — asynchronous, high-performance API framework
- **Python** — application logic, ingestion, and analytics pipelines
- **Uvicorn** — ASGI server and runtime observability

### Data Layer
- **PostgreSQL** — cloud-hosted relational database
- **SQLAlchemy 2.0** — ORM for structured and maintainable database access
- **Pydantic** — schema validation and request/response modeling

### Intelligence & Automation
- **Hugging Face Transformers** — semantic representation of problem statements
- **Sentence-Transformers** — embedding-based similarity search
- **PyTorch** — model inference for semantic classification
- **Custom Python ETL scripts** — ingestion, normalization, and enrichment pipelines

### Infrastructure
- **Render** — backend hosting and managed PostgreSQL deployment
- **CORS Middleware** — controlled cross-origin access for the frontend

---

## 🧠 AI & Machine Learning Pipeline

The API includes an automated tagging engine designed to structure raw interview data into searchable DSA intelligence.

### Vector Embeddings
Problem descriptions are converted into dense semantic vectors using transformer-based embedding models.

### Semantic Inference
The tagging layer compares new or unclassified questions against the existing pattern corpus to infer the most relevant DSA category.

### Efficient Similarity Search
Embedding similarity is used to map ambiguous problems to the closest algorithmic pattern with high speed and consistency.

### Data Enrichment
The auto-tagger improves dataset coverage by filling missing tags and reducing manual labeling overhead.

---

## 📡 Core Endpoints

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/companies` | Returns a list of all indexed companies |
| `GET` | `/companies/{company}/top-patterns` | Returns aggregated DSA pattern frequency for a specific company |
| `GET` | `/roadmap/generate` | Generates a prioritized study sequence based on interview trends |

---

## ⚙️ Data Pipelines

### `ingest_dsa_patterns.py`
Automated ingestion pipeline for batch processing CSV records into the database.

Responsibilities:
- Read raw source files
- Clean and normalize records
- Validate schema consistency
- Insert structured data into PostgreSQL

### `auto_tagger.py`
Semantic classification script used to assign missing DSA tags.

Responsibilities:
- Generate embeddings from problem statements
- Compare semantic similarity across known patterns
- Assign the most relevant tag
- Improve dataset consistency at scale

### Validation & Integrity Checks
Additional checks ensure the data remains consistent, deduplicated, and ready for analytics.

---

## 🚀 Engineering Highlights

### High-Throughput API Design
- Built with FastAPI for asynchronous request handling
- Supports concurrent dashboard queries with minimal latency
- Structured for clean separation between routes, services, and data access

### Data Reliability
- Pydantic-based validation enforces strict schemas
- SQLAlchemy keeps database interactions maintainable and type-safe
- Automated scripts help preserve quality across 18,000+ records

### Intelligent Analytics Pipeline
- ETL workflow transforms raw data into structured insights
- Semantic auto-tagging bridges unstructured interview questions and DSA patterns
- Company-level aggregation supports focused interview preparation

### Scalability
- PostgreSQL indexing supports efficient lookups and analytics queries
- Prepared query patterns improve repeat performance
- Designed to handle growth in both dataset size and request volume

### Observability & Security
- Uvicorn logs provide runtime visibility
- CORS is restricted to trusted frontend origins
- Input validation reduces malformed request risk

---

## 🔒 Security

- CORS configured for frontend communication
- Request and response validation via Pydantic
- Structured API boundaries
- Safe separation between data processing and client-side rendering

---

## 🚀 Deployment

The API is deployed on **Render** with a managed **PostgreSQL** instance.

Deployment notes:
- Web service hosted on Render
- Cloud database managed separately
- Frontend communicates via authenticated/approved cross-origin requests
- Environment variables used for sensitive configuration

---

## 🚦 Local Development Setup


### 1. Create a Virtual Environment

Create an isolated Python environment for the project.

```bash
python -m venv .venv
```

Activate the virtual environment:

**Linux / macOS**

```bash
source .venv/bin/activate
```

**Windows**

```bash
.venv\Scripts\activate
```

---

### 2. Install Dependencies

Install all required Python packages.

```bash
pip install -r requirements.txt
```

---

### 3. Configure Environment Variables

Create a `.env` file in the project root and configure your runtime settings.

Example:

```env
DATABASE_URL=postgresql://user:password@host:port/database
CORS_ORIGINS=https://leetsight-delta.vercel.app
```

---

### 4. Start the Development Server

Run the FastAPI application with hot reloading enabled.

```bash
uvicorn app.main:app --reload
```

---

# 📁 Project Structure

```text
dsa-miner-api/
│
├── app/
│   ├── routes/
│   ├── schemas/
│   ├── models/
│   ├── services/
│   ├── database/
│   └── main.py
│
├── scripts/
│   ├── ingest_dsa_patterns.py
│   ├── auto_tagger.py
│   └── validation.py
│
├── requirements.txt
├── .env
└── README.md
```

---

# 📈 Why This Backend Matters

This repository is more than a conventional REST API.

It functions as a **data ingestion and analytics engine** that transforms thousands of raw coding interview records into structured, searchable intelligence for technical interview preparation.

From data ingestion and normalization to semantic pattern classification and real-time analytics, every component is designed to deliver reliable, scalable, and actionable insights to the LeetSight Dashboard.

The combination of **FastAPI**, **PostgreSQL**, **SQLAlchemy**, **Pydantic**, and an automated **AI-powered tagging pipeline** enables the system to maintain high data quality while serving low-latency analytics across **18,000+ interview questions**.

---

# 🚀 Future Improvements

- ⚡ Redis caching for frequently accessed analytics
- 🔐 JWT-based authentication and authorization
- 🔄 Background workers for asynchronous processing
- 🤖 Batch inference pipeline for large-scale AI tagging
- 🧠 Vector database integration for semantic retrieval
- 🚦 API rate limiting and request throttling
- 📊 Prometheus & Grafana monitoring
- 🐳 Docker containerization
- ☸️ Kubernetes deployment support
- 📈 Expanded analytics and reporting endpoints

---

# 📌 Tech Summary

| Category | Technology |
|-----------|------------|
| **Framework** | FastAPI |
| **Language** | Python |
| **ASGI Server** | Uvicorn |
| **Database** | PostgreSQL |
| **ORM** | SQLAlchemy 2.0 |
| **Validation** | Pydantic |
| **Machine Learning** | Hugging Face Transformers |
| **Semantic Similarity** | Sentence-Transformers |
| **Inference Engine** | PyTorch |
| **Deployment** | Render |
| **API Style** | RESTful API |

---

## ⭐ Closing Note

DSA Miner API serves as the intelligence layer behind the LeetSight ecosystem, transforming raw interview data into structured, scalable, and meaningful analytics. By combining efficient data engineering with semantic machine learning techniques, it provides the foundation for company-specific interview insights and personalized preparation strategies.
