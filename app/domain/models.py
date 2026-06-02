import uuid
from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    ForeignKey,
    Boolean,
    Float,
    DateTime,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship, declarative_base
from pgvector.sqlalchemy import Vector
from datetime import datetime

Base = declarative_base()

# =========================
# User Model
# =========================
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True, nullable=False, index=True)
    hashed_password = Column(String, nullable=False)
    role = Column(String, default="analyst")  # admin, analyst, viewer
    created_at = Column(DateTime, default=datetime.utcnow)

    sessions = relationship("ChatSession", back_populates="user")
    connections = relationship("DatabaseConnection", back_populates="user")


# =========================
# Database Connection Model
# =========================
class DatabaseConnection(Base):
    __tablename__ = "database_connections"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    name = Column(String, nullable=False)
    db_type = Column(String, default="postgresql")
    host = Column(String, nullable=False)
    port = Column(Integer, default=5432)
    database = Column(String, nullable=False)
    username = Column(String, nullable=False)
    encrypted_password = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    # Snowflake-specific
    account = Column(String, nullable=True)
    warehouse = Column(String, nullable=True)
    role = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_synced = Column(DateTime, nullable=True)

    user = relationship("User", back_populates="connections")
    schemas = relationship("Schema", back_populates="connection", cascade="all, delete-orphan")
    quality_scores = relationship("DataQualityScore", back_populates="connection", cascade="all, delete-orphan")
    analysis_cache = relationship("AIAnalysisCache", back_populates="connection", cascade="all, delete-orphan")
    export_jobs = relationship("ExportJob", back_populates="connection", cascade="all, delete-orphan")


# =========================
# Source Connection Model
# =========================
class SourceConnection(Base):
    __tablename__ = "source_connections"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    db_type = Column(String, nullable=False)  # postgresql, mysql, mongodb, snowflake
    encrypted_credentials = Column(Text, nullable=False)
    is_active = Column(Boolean, default=True)
    last_tested_at = Column(DateTime, nullable=True)
    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)

    # Added relationship pointer
    creator = relationship("User")


# =========================
# Schema Model
# =========================
class Schema(Base):
    __tablename__ = "schemas"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    connection_id = Column(Integer, ForeignKey("database_connections.id"), nullable=True)

    __table_args__ = (
        UniqueConstraint("name", "connection_id", name="unique_schema_per_connection"),
    )

    connection = relationship("DatabaseConnection", back_populates="schemas")
    tables = relationship("Table", back_populates="schema", cascade="all, delete-orphan")


# =========================
# Table Model
# =========================
class Table(Base):
    __tablename__ = "tables"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    schema_id = Column(Integer, ForeignKey("schemas.id"))
    row_count = Column(Integer, nullable=True)

    schema = relationship("Schema", back_populates="tables")
    columns = relationship("ColumnModel", back_populates="table", cascade="all, delete-orphan")
    relationships = relationship("Relationship", back_populates="table", cascade="all, delete-orphan")


# =========================
# Column Model
# =========================
class ColumnModel(Base):
    __tablename__ = "columns"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    data_type = Column(String)
    is_nullable = Column(Boolean)
    is_primary_key = Column(Boolean, default=False)
    is_foreign_key = Column(Boolean, default=False)
    ai_description = Column(Text, nullable=True)

    table_id = Column(Integer, ForeignKey("tables.id"))
    table = relationship("Table", back_populates="columns")

    profile = relationship("ColumnProfile", uselist=False, back_populates="column", cascade="all, delete-orphan")


# =========================
# Relationship Model
# =========================
class Relationship(Base):
    __tablename__ = "relationships"

    id = Column(Integer, primary_key=True)
    source_table = Column(String)
    source_column = Column(String)
    target_table = Column(String)
    target_column = Column(String)

    table_id = Column(Integer, ForeignKey("tables.id"))
    table = relationship("Table", back_populates="relationships")


# =========================
# Column Profiling Model
# =========================
class ColumnProfile(Base):
    __tablename__ = "column_profiles"

    id = Column(Integer, primary_key=True)
    null_percentage = Column(Float)
    distinct_count = Column(Integer)
    min_value = Column(String)
    max_value = Column(String)
    mean = Column(Float)

    column_id = Column(Integer, ForeignKey("columns.id"))
    column = relationship("ColumnModel", back_populates="profile")


# =========================
# Documentation Model
# =========================
class Documentation(Base):
    __tablename__ = "documentation"

    __table_args__ = (
        UniqueConstraint("entity_type", "entity_id", name="unique_documentation_entity"),
    )

    id = Column(Integer, primary_key=True)
    connection_id = Column(String(36), ForeignKey("source_connections.id"), nullable=True)
    entity_type = Column(String)
    entity_id = Column(Integer)
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)


# =========================
# Embedding Model
# =========================
class Embedding(Base):
    __tablename__ = "embeddings"

    __table_args__ = (
        UniqueConstraint("entity_type", "entity_id", name="unique_embedding_entity"),
    )

    id = Column(Integer, primary_key=True)
    connection_id = Column(String(36), ForeignKey("source_connections.id"), nullable=True)
    entity_type = Column(String)
    entity_id = Column(Integer)
    vector = Column(Vector(384))


# =========================
# Chat Session Model
# =========================
class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="sessions")

    messages = relationship(
        "ChatMessage",
        back_populates="session",
        cascade="all, delete-orphan"
    )


# =========================
# Chat Message Model
# =========================
class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True)
    session_id = Column(Integer, ForeignKey("chat_sessions.id"))
    role = Column(String)
    content = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    session = relationship("ChatSession", back_populates="messages")


# =========================
# AI Analysis Cache Model
# =========================
class AIAnalysisCache(Base):
    __tablename__ = "ai_analysis_cache"

    id = Column(Integer, primary_key=True)
    connection_id = Column(Integer, ForeignKey("database_connections.id"))
    entity_type = Column(String)      # "database", "table", "column"
    entity_name = Column(String)
    analysis_type = Column(String)    # "overview", "quality", "documentation"
    result_json = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)

    connection = relationship("DatabaseConnection", back_populates="analysis_cache")


# =========================
# Data Quality Score Model
# =========================
class DataQualityScore(Base):
    __tablename__ = "data_quality_scores"

    id = Column(Integer, primary_key=True)
    connection_id = Column(Integer, ForeignKey("database_connections.id"))
    table_name = Column(String)
    completeness = Column(Float)
    uniqueness = Column(Float)
    overall_score = Column(Float)
    details_json = Column(Text)
    computed_at = Column(DateTime, default=datetime.utcnow)

    connection = relationship("DatabaseConnection", back_populates="quality_scores")


# =========================
# Export Job Model
# =========================
class ExportJob(Base):
    __tablename__ = "export_jobs"

    id = Column(Integer, primary_key=True)
    connection_id = Column(Integer, ForeignKey("database_connections.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    format = Column(String)           # json, markdown, html, pdf
    status = Column(String, default="pending")  # pending, running, completed, failed
    file_path = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    connection = relationship("DatabaseConnection", back_populates="export_jobs")


# =========================
# Annotation Model (Feature 6)
# =========================
class Annotation(Base):
    __tablename__ = "annotations"

    id = Column(Integer, primary_key=True)
    table_name = Column(String, nullable=False)
    column_name = Column(String, nullable=True)  # NULL = table-level annotation
    content = Column(Text, nullable=False)
    author_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    author = relationship("User")


# =========================
# Column Lineage Model (Feature 2)
# =========================
class ColumnLineage(Base):
    __tablename__ = "column_lineage"

    id = Column(Integer, primary_key=True)
    source_table = Column(String, nullable=False)
    source_column = Column(String, nullable=False)
    target_table = Column(String, nullable=False)
    target_column = Column(String, nullable=False)
    transformation_expression = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


# =========================
# Profiling History Model (Feature 3)
# =========================
class ProfilingHistory(Base):
    __tablename__ = "profiling_history"

    id = Column(Integer, primary_key=True)
    column_id = Column(Integer, ForeignKey("columns.id"), nullable=False)
    null_rate = Column(Float, nullable=True)
    duplicate_rate = Column(Float, nullable=True)
    mean = Column(Float, nullable=True)
    std_dev = Column(Float, nullable=True)
    profiled_at = Column(DateTime, default=datetime.utcnow)

    column = relationship("ColumnModel")


# =========================
# Anomaly Alert Model (Feature 3)
# =========================
class AnomalyAlert(Base):
    __tablename__ = "anomaly_alerts"

    id = Column(Integer, primary_key=True)
    column_id = Column(Integer, ForeignKey("columns.id"), nullable=False)
    table_name = Column(String, nullable=False)
    column_name = Column(String, nullable=False)
    alert_type = Column(String, nullable=False)  # null_rate_spike, duplicate_rate_spike, mean_shift
    message = Column(Text, nullable=False)
    severity = Column(String, default="warning")  # info, warning, critical
    dismissed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    column = relationship("ColumnModel")


# =========================
# Column Permission Model (Feature 7)
# =========================
class ColumnPermission(Base):
    __tablename__ = "column_permissions"

    id = Column(Integer, primary_key=True)
    role = Column(String, nullable=False)
    table_name = Column(String, nullable=False)
    column_name = Column(String, nullable=False)
    allow = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
