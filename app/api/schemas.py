from pydantic import BaseModel, EmailStr
from typing import Optional, List, Any
from datetime import datetime


# =========================
# Chat Schemas
# =========================
class ChatRequest(BaseModel):
    question: str
    connection_id: Optional[int] = None


class SQLResult(BaseModel):
    columns: List[str]
    rows: List[List[Any]]


class ChatResponse(BaseModel):
    session_id: int
    mode: str
    answer: str
    sql: Optional[str] = None
    explanation: Optional[str] = None
    result: Optional[SQLResult] = None
    confidence: Optional[dict] = None


# =========================
# Auth Schemas
# =========================
class UserSignup(BaseModel):
    email: EmailStr
    password: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


# =========================
# Connection Schemas
# =========================
class ConnectionCreate(BaseModel):
    name: str
    db_type: str = "postgresql"
    host: Optional[str] = None
    port: Optional[int] = None
    database: str
    username: Optional[str] = None
    password: Optional[str] = None
    # Snowflake
    account: Optional[str] = None
    warehouse: Optional[str] = None
    role: Optional[str] = None


class ConnectionTest(BaseModel):
    db_type: str = "postgresql"
    host: Optional[str] = None
    port: Optional[int] = None
    database: str
    username: Optional[str] = None
    password: Optional[str] = None
    # Snowflake
    account: Optional[str] = None
    warehouse: Optional[str] = None
    role: Optional[str] = None


class ConnectionResponse(BaseModel):
    id: int
    name: str
    db_type: str
    host: str
    port: int
    database: str
    username: str
    is_active: bool
    created_at: Optional[datetime] = None
    last_synced: Optional[datetime] = None

    @classmethod
    def from_model(cls, m):
        return cls(
            id=m.id,
            name=m.name,
            db_type=m.db_type,
            host=m.host,
            port=m.port,
            database=m.database,
            username=m.username,
            is_active=m.is_active,
            created_at=m.created_at,
            last_synced=m.last_synced,
        )


class ConnectionListResponse(BaseModel):
    connections: List[ConnectionResponse]


class TestConnectionResponse(BaseModel):
    status: str
    version: Optional[str] = None
    detail: Optional[str] = None


class SyncResponse(BaseModel):
    schemas: int
    tables: int
    columns: int
    relationships: int


# =========================
# Dashboard Schemas
# =========================
class OverviewResponse(BaseModel):
    total_tables: int
    total_columns: int
    total_rows: int
    total_relationships: int
    schemas: List[str]


# =========================
# Table Schemas
# =========================
class ColumnInfo(BaseModel):
    name: str
    data_type: Optional[str] = None
    is_nullable: Optional[bool] = None
    is_primary_key: bool = False
    is_foreign_key: bool = False
    ai_description: Optional[str] = None


class RelationshipInfo(BaseModel):
    source_table: str
    source_column: str
    target_table: str
    target_column: str


class TableSummary(BaseModel):
    name: str
    schema_name: str
    column_count: int
    row_count: Optional[int] = None
    relationship_count: int


class TableDetail(BaseModel):
    name: str
    schema_name: str
    row_count: Optional[int] = None
    columns: List[ColumnInfo]
    relationships: List[RelationshipInfo]


class TableListResponse(BaseModel):
    tables: List[TableSummary]
    total: int


class SampleDataResponse(BaseModel):
    columns: List[str]
    rows: List[List[Any]]
    total_rows: Optional[int] = None


# =========================
# Quality Schemas
# =========================
class TableQualityScore(BaseModel):
    table_name: str
    completeness: float
    uniqueness: float
    overall_score: float
    details: Optional[Any] = None


class QualityResponse(BaseModel):
    connection_id: int
    overall_score: float
    tables: List[TableQualityScore]


# =========================
# AI Analysis Schemas
# =========================
class AIAnalysisRequest(BaseModel):
    force_refresh: bool = False


class DatabaseAnalysisResponse(BaseModel):
    business_purpose: Optional[str] = None
    domain: Optional[str] = None
    model_type: Optional[str] = None
    architecture_observations: Optional[List[str]] = None
    key_entity_groups: Optional[List[str]] = None
    cached: bool = False


class TableAnalysisResponse(BaseModel):
    table_name: str
    business_context: Optional[str] = None
    key_insights: Optional[List[str]] = None
    recommendations: Optional[List[str]] = None
    cached: bool = False


# =========================
# Export Schemas
# =========================
class ExportRequest(BaseModel):
    format: str  # json, markdown, html, pdf


class ExportStatusResponse(BaseModel):
    job_id: int
    status: str
    format: str
    file_path: Optional[str] = None
    created_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

