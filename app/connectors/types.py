from dataclasses import dataclass
from typing import Any, List, Optional


@dataclass
class ColumnMeta:
    name: str
    data_type: str
    is_nullable: bool
    is_primary_key: bool = False
    is_foreign_key: bool = False
    description: Optional[str] = None


@dataclass
class QueryResult:
    columns: List[str]
    rows: List[List[Any]]
    error: Optional[str] = None
