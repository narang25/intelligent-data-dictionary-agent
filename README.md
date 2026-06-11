# Intelligent Data Dictionary (Jarvis) 🧠📊

An enterprise-grade, AI-powered Data Dictionary platform designed to connect to multiple disparate data sources, automatically extract schemas, profile data quality, infer data lineage, and provide a conversational interface to query your metadata.

## 🌟 The Vision

Modern data teams struggle with massive, undocumented databases. Our platform bridges the gap between raw data schemas and human understanding. It centralizes metadata into a single searchable, understandable, and well-documented platform, using cutting-edge LLM technology to automatically document tables and generate SQL from natural language.

---

## 🚀 Core Features

- **Automated AI Documentation:** Don't write descriptions manually. Connect a database and let the LLM generate business context, key insights, and descriptions for every table and column.
- **Dual-Brain Chat Interface:** Ask your database questions in plain English. 
  - *Quantitative Intent:* The AI generates SQL, runs it against your database, and returns the tabular result.
  - *Qualitative Intent:* The AI uses RAG (Retrieval-Augmented Generation) with **pgvector** embeddings to answer questions about your schema semantics.
- **Automated Lineage Tracking:** Instantly visualize how data moves through your system. The platform automatically infers lineage from Foreign Keys and renders a beautiful node-based relationship graph.
- **Data Quality Profiling:** Continuously monitors your database health. Calculates completeness (NULL checks) and uniqueness scores, automatically alerting you to anomalies.
- **One-Click Export:** Generate formatted, styled PDF documentation for your entire schema instantly via the Quick Actions dashboard.
- **Universal Connection Architecture:** Natively supports PostgreSQL, MySQL, Snowflake, and MongoDB with a plug-and-play connector factory. 

---

## 🏗️ Tech Stack

**Backend System**
- **Framework:** FastAPI (Python 3.11)
- **Database:** PostgreSQL (with `pgvector` & `pgcrypto`)
- **AI & ML:** Sentence-Transformers (Local Embeddings), pgvector (Vector DB), Groq/OpenAI (LLM reasoning)
- **Task Queue:** Celery + Redis (for asynchronous background AI generation)
- **Security:** AES encryption at rest for database credentials via Python `cryptography` (Fernet)

**Frontend System**
- **Framework:** React + Vite
- **Styling:** Vanilla CSS, Modern Glassmorphism UI, Dark Mode Default
- **Data Viz:** Custom pure SVG interactive network graphs

**Infrastructure**
- **Deployment:** Fully Dockerized (6 containers) utilizing Nginx

---

## 💻 Getting Started

### Prerequisites
- [Docker](https://docs.docker.com/get-docker/)
- [Docker Compose](https://docs.docker.com/compose/install/)

### Installation & Execution

1. **Clone the repository:**
   ```bash
   git clone https://github.com/yourusername/intelligent-data-dictionary.git
   cd intelligent-data-dictionary
   ```

2. **Start the platform via Docker Compose:**
   ```bash
   docker-compose up --build -d
   ```
   *This single command builds all images and spins up the entire microservice architecture:*
   - `jarvis_frontend` (Nginx serving React UI on port 80)
   - `jarvis_api` (FastAPI backend on port 8000)
   - `jarvis_worker` (Celery background task worker)
   - `jarvis_beat` (Celery beat scheduler)
   - `jarvis_redis` (Message broker)
   - `jarvis_db` (Internal PostgreSQL DB storing platform metadata)

3. **Access the Platform:**
   - **Frontend UI:** [http://localhost](http://localhost)
   - **Backend API Docs:** [http://localhost:8000/docs](http://localhost:8000/docs)

*(Note: If connecting to a local database outside of Docker, use `host.docker.internal` as the connection Host instead of `localhost`)*

---

## 🔒 Security & Privacy First
- **Read-Only Safeties:** We enforce strict schema introspection without destructive write access.
- **PII Skipping:** Intelligent profiling automatically bypasses scanning raw values for columns flagged as containing sensitive PII (Passwords, SSNs, Emails) to ensure compliance.
- **Credential Encryption:** All external database passwords and tokens are strongly encrypted via symmetric cryptography before being stored in the metadata database.

---
*Built to make data understandable for everyone.*
