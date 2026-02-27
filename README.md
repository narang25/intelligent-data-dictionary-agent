# API Endpoints

The backend exposes a set of RESTful API endpoints, all prefixed with `/api/` (proxied via Nginx in production):

| Endpoint                | Method | Description                                 |
|------------------------|--------|---------------------------------------------|
| `/api/health`          | GET    | Health check for all services               |
| `/api/auth/signup`     | POST   | User registration                          |
| `/api/auth/login`      | POST   | User authentication                        |
| `/api/chat`            | POST   | Conversational interface (SQL, docs, RAG)   |
| `/api/docs`            | GET    | Documentation search                        |
| `/api/profiling`       | GET    | Data profiling and statistics               |

---

# Frontend

The frontend is a modern, single-page application built with React 18, Vite, TailwindCSS, React Router, and Recharts. Key features include:
- Responsive design with dark/light theme support
- Conversational chat interface for SQL and documentation
- Schema explorer and documentation viewer
- All API requests are routed through `/api/` (Nginx reverse proxy)

---

# Dataset

IDD uses the Olist Brazilian E-commerce dataset for demonstration and benchmarking. The dataset includes the following tables:
- olist_customers_dataset.csv
- olist_sellers_dataset.csv
- olist_products_dataset.csv
- olist_orders_dataset.csv
- olist_order_items_dataset.csv
- olist_order_payments_dataset.csv
- olist_order_reviews_dataset.csv
- olist_geolocation_dataset.csv

This dataset provides a realistic, relational schema for testing AI-powered SQL generation, documentation, and profiling features.

---

# Environment Variables

The following environment variables are required for configuration:

| Variable         | Description                                 |
|------------------|---------------------------------------------|
| `DB_PASSWORD`    | PostgreSQL database password                |
| `GROQ_API_KEY`   | Groq LLM API key                           |
| `SECRET_KEY`     | FastAPI application secret                  |
| `CORS_ORIGINS`   | Allowed CORS origins (comma-separated list) |

---

# Credits

This project was developed with contributions and support from the open-source community. Special thanks to **vanshikataya** for their significant contributions and support.

- [Olist Brazilian E-commerce Dataset](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce)
- [Groq LLM API](https://console.groq.com/)
- [Sentence Transformers](https://www.sbert.net/)
- [pgvector](https://github.com/pgvector/pgvector)
# Motivation

Modern data teams face challenges in understanding, documenting, and querying complex data warehouses. IDD addresses these challenges by combining AI-driven documentation, semantic search, and natural language interfaces, enabling:
- Rapid onboarding for new team members
- Self-service analytics for business users
- Consistent, up-to-date data documentation
- Reduced dependency on manual SQL writing

---

# Use Cases

- **Data Discovery**: Instantly search and understand tables, columns, and relationships.
- **Self-Service Analytics**: Empower non-technical users to generate SQL and insights via chat.
- **Data Governance**: Maintain a living data dictionary with AI-generated and human-curated docs.
- **Data Profiling**: Quickly assess data quality and completeness for any table or column.
- **AI-Driven Documentation**: Automatically generate and update documentation as schemas evolve.

---

# Security & Privacy

- All API endpoints require authentication (JWT-based)
- Sensitive credentials and API keys are managed via environment variables
- No user data or queries are logged or shared externally by default
- Supports secure deployment behind firewalls and VPNs

---

# Extensibility

- **Pluggable LLMs**: Swap out Groq for OpenAI, Azure, or local models
- **Custom Connectors**: Add support for additional databases (e.g., MySQL, Snowflake)
- **UI Customization**: The frontend is modular and can be themed or extended
- **API Hooks**: Integrate with CI/CD, data quality tools, or observability platforms

---

# Contributing

Contributions are welcome! To contribute:
1. Fork the repository
2. Create a new branch for your feature or bugfix
3. Write clear, well-documented code and tests
4. Submit a pull request with a detailed description

Please see `CONTRIBUTING.md` for guidelines and code of conduct.

---

# Frequently Asked Questions (FAQ)

**Q: Can I use my own LLM or API key?**
A: Yes, the backend is designed to support pluggable LLM providers. Update your environment variables accordingly.

**Q: Is this suitable for production?**
A: Yes, the system is containerized, supports health checks, and can be deployed on any modern cloud or on-prem infrastructure.

**Q: How do I add a new data source?**
A: Implement a new connector in the `connectors/` directory and register it in the backend service layer.

**Q: Does it support multi-tenancy?**
A: Not out-of-the-box, but the architecture allows for extension to multi-tenant scenarios.

---

# Contact & Support

- For issues, please use the GitHub Issues tracker.
- For feature requests or partnership inquiries, contact the maintainer at [nikhil.narang25@gmail.com](mailto:nikhil.narang25@gmail.com)

---
# Intelligent Data Dictionary (IDD)

A full-stack, production-ready AI-powered data dictionary and SQL generation platform for modern data teams. Built with FastAPI, React, PostgreSQL (pgvector), Celery, Redis, and advanced LLMs (Groq, Sentence Transformers).


## Features



## Architecture

```
[ React (Vite) ] <--> [ Nginx ] <--> [ FastAPI (Groq, SQLAlchemy, Celery) ] <--> [ PostgreSQL + pgvector ]
                                             |                                 |
                                         [ Redis ]                        [ Sentence Transformers ]
```


## Quickstart (Local)

1. **Clone the repo**

```bash
git clone https://github.com/narang25/intelligent-data-dictionary-agent.git
cd intelligent-data-dictionary-agent
```

2. **Set up environment**

  - `DB_PASSWORD=...`
  - `GROQ_API_KEY=...` (get from https://console.groq.com/)
  - `SECRET_KEY=...`
  - `CORS_ORIGINS=http://localhost`

3. **Start all services**

```bash
docker compose up --build
```

4. **Load Olist Data**


```bash
bash deploy/init-data.sh
```





# Intelligent Data Dictionary (IDD)

## Overview

Intelligent Data Dictionary (IDD) is a robust, production-grade platform designed to empower data teams with AI-driven data discovery, documentation, and natural language SQL generation. The system integrates modern backend and frontend technologies, advanced language models, and scalable infrastructure to deliver a seamless experience for data exploration and analytics.

---

## Key Features

- **AI-Powered SQL Generation**: Transform natural language queries into accurate SQL statements using state-of-the-art LLMs (Groq Llama-4-Scout-17B).
- **Retrieval-Augmented Generation (RAG) Documentation**: Automatically generate and retrieve comprehensive documentation for tables and columns, leveraging both AI and existing metadata.
- **Semantic Vector Search**: Perform semantic search over documentation and schema using pgvector and sentence-transformers for highly relevant results.
- **Automated Data Profiling**: Generate detailed column statistics, data types, null counts, unique values, and more for all tables.
- **Conversational Chat Interface**: Interact with your data warehouse through a modern chat UI, supporting both SQL and documentation queries.
- **Modern UI/UX**: Responsive React frontend with dark/light theme support, intuitive navigation, and real-time chat.
- **Admin Data Loader**: Bulk ingestion of the Olist Brazilian e-commerce dataset for demonstration and benchmarking.
- **Containerized Microservices**: Fully dockerized architecture including API, frontend, database, Redis, and Celery worker for scalable deployments.
- **Production-Ready Operations**: Health checks, CORS configuration, Nginx reverse proxy, environment-based configuration, and robust error handling.

---

## System Architecture

```
┌────────────┐      ┌────────┐      ┌──────────────┐      ┌────────────────────┐
│  Frontend  │ <--> │ Nginx  │ <--> │   FastAPI    │ <--> │ PostgreSQL + pgvector│
│  (React)   │      │        │      │ (Groq, Celery│      │   (Vector Search)  │
└────────────┘      └────────┘      └──────────────┘      └────────────────────┘
                   │
                   ▼
                 [ Redis ]
                   │
                   ▼
            [ Sentence Transformers ]
```

---


## API Reference

All endpoints are prefixed with `/api/` (handled by Nginx reverse proxy).

| Endpoint                | Method | Description                                 |
|------------------------|--------|---------------------------------------------|
| `/api/health`          | GET    | Health check for all services               |
| `/api/auth/signup`     | POST   | User registration                          |
| `/api/auth/login`      | POST   | User authentication                        |
| `/api/chat`            | POST   | Conversational interface (SQL, docs, RAG)   |
| `/api/docs`            | GET    | Documentation search                        |
| `/api/profiling`       | GET    | Data profiling and statistics               |

---

## Frontend Application

- Built with React 18, Vite, TailwindCSS, React Router, and Recharts
- All API requests are routed through `/api/` (Nginx reverse proxy)
- Features include theme switching, chat interface, schema explorer, and documentation viewer
- Responsive design for desktop and mobile

---

## Dataset Details

The platform uses the Olist Brazilian E-commerce dataset for demonstration and benchmarking. The dataset includes the following tables:

- `olist_customers_dataset.csv`
- `olist_sellers_dataset.csv`
- `olist_products_dataset.csv`
- `olist_orders_dataset.csv`
- `olist_order_items_dataset.csv`
- `olist_order_payments_dataset.csv`
- `olist_order_reviews_dataset.csv`
- `olist_geolocation_dataset.csv`

Total size: ~120MB. Schema includes customers, sellers, products, orders, order items, payments, reviews, and geolocation.

---

## Environment Variables

| Variable         | Description                                 |
|------------------|---------------------------------------------|
| `DB_PASSWORD`    | PostgreSQL database password                |
| `GROQ_API_KEY`   | Groq LLM API key                           |
| `SECRET_KEY`     | FastAPI application secret                  |
| `CORS_ORIGINS`   | Allowed CORS origins (comma-separated list) |

---

## System Requirements

- Docker 24+
- Docker Compose v2+
- Python 3.11+ (for development only)
- Node.js 20+ (for frontend development only)

---

## Credits and Acknowledgements

- [Olist Brazilian E-commerce Dataset](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce)
- [Groq LLM API](https://console.groq.com/)
- [Sentence Transformers](https://www.sbert.net/)
- [pgvector](https://github.com/pgvector/pgvector)

---

## License

This project is licensed under the MIT License.
