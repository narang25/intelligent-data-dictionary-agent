# Intelligent Data Dictionary

An intelligent, AI-powered Data Dictionary platform designed to connect to multiple disparate data sources, automatically extract schemas, profile data quality, provide automated lineage, and offer a conversational interface to query your metadata.

## Overview

The platform allows data teams to centralize their database metadata into a single searchable, understandable, and well-documented platform. It supports seamless integration with various SQL and NoSQL engines, providing a unified dashboard for all your data assets.

## Supported Connections

The platform natively supports the following database systems:
1. **PostgreSQL** 🐘
2. **MySQL** 🐬
3. **Snowflake** ❄️
4. **MongoDB** 🍃

*The connector architecture is plug-and-play, meaning new data sources can easily be added to the registry.*

## Features

- **Automated Schema Syncing:** Extracts schemas, tables, collections, columns, and relationships (Foreign Keys) directly from the source databases.
- **Unified UI Dashboard:** A modern, React-based UI to manage your connections, browse tables, and sync metadata.
- **Data Quality Profiling:** Built-in hooks to score your data quality (completeness, uniqueness).
- **Data Lineage Tracking:** Track how data moves through your system to easily assess the impact of schema changes.
- **Secure by Default:** Database credentials (including passwords and connection strings) are encrypted at rest using Python `cryptography` (Fernet).
- **Dockerized Architecture:** The entire stack (Frontend, API, Worker, Beat, Redis, PostgreSQL metadata DB) runs via Docker Compose for easy deployment.

## Tech Stack

### Backend
- **Framework:** FastAPI (Python 3.11)
- **ORM:** SQLAlchemy (Async + Sync)
- **Database:** PostgreSQL (with `pgvector` for future AI embeddings)
- **Task Queue:** Celery + Redis (for background syncs and profiling)
- **Encryption:** `cryptography` (Fernet)

### Frontend
- **Framework:** React + Vite
- **Styling:** Vanilla CSS + Modern Glassmorphism UI
- **Server:** Nginx (Alpine)

## Getting Started

### Prerequisites
- [Docker](https://docs.docker.com/get-docker/)
- [Docker Compose](https://docs.docker.com/compose/install/)

### Installation & Execution

1. **Clone the repository**

2. **Start the platform via Docker Compose**
   ```bash
   docker-compose up --build -d
   ```
   *This command builds all images and spins up 6 containers:*
   - `jarvis_frontend` (Nginx serving React UI on port 80)
   - `jarvis_api` (FastAPI backend on port 8000)
   - `jarvis_worker` (Celery background task worker)
   - `jarvis_beat` (Celery beat scheduler)
   - `jarvis_redis` (Message broker)
   - `jarvis_db` (Internal PostgreSQL DB storing platform metadata)

3. **Access the Platform**
   - **Frontend UI:** [http://localhost](http://localhost)
   - **Backend API Docs:** [http://localhost:8000/docs](http://localhost:8000/docs)

### Connecting to Local Databases
If you are trying to connect to a database running on your local host machine (e.g., a local MySQL or MongoDB instance running outside of Docker), use `host.docker.internal` as the Host instead of `localhost`.

## Architecture Note for Frontend Developers
- The Connections API utilizes a centralized `ConnectionService` which encrypts parameters and relies on a `ConnectorFactory` pattern.
- In the React frontend, connection forms dynamically render fields based on the selected `db_type` (handled in `ConnectionsPage.jsx`).
- The entire UI relies heavily on context (`ConnectionContext.jsx`) to keep track of the currently active database for viewing tables and lineage.

---
*Built for modern data teams.*
