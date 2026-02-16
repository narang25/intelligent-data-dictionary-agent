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
# Schema Model
# =========================
class Schema(Base):
    __tablename__ = "schemas"

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)

    tables = relationship("Table", back_populates="schema")


# =========================
# Table Model
# =========================
class Table(Base):
    __tablename__ = "tables"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    schema_id = Column(Integer, ForeignKey("schemas.id"))

    schema = relationship("Schema", back_populates="tables")
    columns = relationship("ColumnModel", back_populates="table")
    relationships = relationship("Relationship", back_populates="table")


# =========================
# Column Model
# =========================
class ColumnModel(Base):
    __tablename__ = "columns"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    data_type = Column(String)
    is_nullable = Column(Boolean)

    table_id = Column(Integer, ForeignKey("tables.id"))
    table = relationship("Table", back_populates="columns")

    profile = relationship(
        "ColumnProfile",
        uselist=False,
        back_populates="column"
    )


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
        UniqueConstraint(
            "entity_type",
            "entity_id",
            name="unique_documentation_entity",
        ),
    )

    id = Column(Integer, primary_key=True)
    entity_type = Column(String)  # table / column
    entity_id = Column(Integer)
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)


# =========================
# Embedding Model
# =========================
class Embedding(Base):
    __tablename__ = "embeddings"

    __table_args__ = (
        UniqueConstraint(
            "entity_type",
            "entity_id",
            name="unique_embedding_entity",
        ),
    )

    id = Column(Integer, primary_key=True)
    entity_type = Column(String)
    entity_id = Column(Integer)
    vector = Column(Vector(384))


# =========================
# Chat Session Model
# =========================
class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id = Column(Integer, primary_key=True)
    created_at = Column(DateTime, default=datetime.utcnow)

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
    role = Column(String)  # user / assistant
    content = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    session = relationship("ChatSession", back_populates="messages")
