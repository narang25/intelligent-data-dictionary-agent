# Intelligent Data Dictionary (IDD) - Multi-Database Architecture Update

This document summarizes the recent architectural updates to transition the Intelligent Data Dictionary from a monolithic PostgreSQL-only analyzer to a fully decoupled, multi-database introspection engine. 

## ✅ What is Working (Currently Implemented)

1. **Unified Connector Interface**
   - We introduced an abstract `BaseConnector` pattern to standardize schema introspection across diverse SQL dialects.
   - Fully fledged connectors are implemented for **PostgreSQL, MySQL, Snowflake, and BigQuery**.

2. **Secure Connection Registry**
   - Added a `SourceConnection` model to handle UUID-based multi-tenant sources.
   - Credentials (including Service Account JSONs for BigQuery and passwords for Snowflake) are securely encrypted at rest using Python `cryptography` (Fernet) and cached in a singleton runtime registry (`ConnectionRegistry`).

3. **Namespaced Vector Store**
   - Because `pgvector` relies on PostgreSQL, we successfully decoupled the vector search layer from the "Source Database".
   - The primary IDD database now stores embeddings across a `connection_id` namespace, allowing chat sessions to dynamically restrict RAG queries to only the tables matching the user's active connection.

4. **Multi-Database UI Setup**
   - The frontend's Connection Page has been rebuilt to support dynamic inputs (e.g., prompting for Account Identifier for Snowflake, Project ID for BigQuery).
   - "Test Connection" and "Sync Connection" flows are integrated using non-blocking Celery background tasks (`run_source_sync`).

5. **Dialect-Aware LLM SQL Generation**
   - The unified chat service passes the active dialect into the prompt instructions to guarantee generated SQL matches the active database's syntax.

---

## 🚧 What is Not Fully Working (To Include in Upcoming Product)

The foundational multi-database logic is stable, but there are necessary steps remaining before legacy features achieve parity over the new UI:

1. **Frontend View Migrations (Tables, Profiling, Dashboard)**
   - **Current State**: The legacy pages (`/tables`, `/quality`) still rely on an older `DatabaseConnection` model matching by Integer ID. 
   - **Upcoming Feature**: We need to port these APIs to query remote databases dynamically or proxy schema displays off the new string-UUID `SourceConnection` standard.

2. **Cross-Dialect Profiling Adapters (Feature 3)**
   - **Current State**: Data quality tasks currently execute raw PostgreSQL-flavor SQL (e.g., `COUNT(DISTINCT x) FILTER ...`). 
   - **Upcoming Feature**: The Celery profiling background tasks need to be adapted to route through `BaseConnector` implementations to support dialect-specific analytic queries.

3. **Real-time Schema Sync (Feature 1)**
   - **Upcoming Feature**: Currently, the schema introspection (`run_source_sync`) is triggered manually. The upcoming product will implement Database CDC (Change Data Capture) or Postgres LISTEN/NOTIFY pipelines to auto-refresh vectors.

4. **Data Lineage Tracking (Feature 2)**
   - **Upcoming Feature**: Storing parsed query tree transformations (`dbt`-style lineage tracking) for generated columns.

5. **Column-Level Permissions and Guardrails (Feature 7)**
   - **Upcoming Feature**: Implementing a rules engine so that certain columns can be marked "off limits" (e.g. PII) inside the `BaseConnector` interface, effectively preventing the LLM from fetching or querying them.

---

### Stability Note
All API backend endpoints related to testing connections, syncing tasks, and executing namespaced LLM queries are fundamentally stable. The previous 502/500 backend startup crashes related to missing configuration module imports (`app.core.config`) have been fully resolved. 
