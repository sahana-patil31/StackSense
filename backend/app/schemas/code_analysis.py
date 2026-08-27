from datetime import datetime
from typing import Any, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class AnalyzeRepositoryRequest(BaseModel):
    path: Optional[str] = Field(default=None, description="Local filesystem path of repository source directory")


class CodeFileResponse(BaseModel):
    id: str
    repository_id: str
    path: str
    language: str
    size: int
    analysis_status: str
    analysis_error: Optional[str] = None
    analyzed_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CodeEntityResponse(BaseModel):
    id: str
    repository_id: str
    file_id: str
    parent_entity_id: Optional[str] = None
    entity_type: str  # FILE, MODULE, FUNCTION, CLASS, METHOD
    name: str
    qualified_name: Optional[str] = None
    start_line: int
    end_line: int

    model_config = ConfigDict(from_attributes=True)


class CodeRelationshipResponse(BaseModel):
    id: str
    repository_id: str
    source_entity_id: str
    target_entity_id: Optional[str] = None
    relationship_type: str  # CONTAINS, IMPORTS, CALLS, DEFINES
    resolved: bool
    raw_target: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class AnalysisRunResponse(BaseModel):
    id: str
    repository_id: str
    status: str
    files_discovered: int
    files_analyzed: int
    entities_found: int
    relationships_found: int
    files_failed: int
    started_at: datetime
    completed_at: Optional[datetime] = None
    error_summary: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class GraphNode(BaseModel):
    id: str
    label: str
    type: str  # repository, file, module, class, function, method
    file_id: Optional[str] = None
    file_path: Optional[str] = None
    name: str
    qualified_name: Optional[str] = None
    start_line: Optional[int] = None
    end_line: Optional[int] = None


class GraphEdge(BaseModel):
    id: str
    source: str
    target: str
    relationship_type: str  # CONTAINS, IMPORTS, CALLS, DEFINES
    resolved: bool
    raw_target: Optional[str] = None


class GraphResponse(BaseModel):
    nodes: List[GraphNode]
    edges: List[GraphEdge]
