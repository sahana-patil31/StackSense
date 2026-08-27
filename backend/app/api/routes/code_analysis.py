from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import require_engineer
from app.models.analysis_run import AnalysisRun
from app.models.code_entity import CodeEntity
from app.models.code_file import CodeFile
from app.models.code_relationship import CodeRelationship
from app.models.repository import Repository
from app.schemas.code_analysis import (
    AnalysisRunResponse,
    AnalyzeRepositoryRequest,
    CodeEntityResponse,
    CodeFileResponse,
    CodeRelationshipResponse,
    GraphResponse,
)
from app.services.code_analysis.analyzer import analyze_repository
from app.services.code_analysis.graph_builder import build_dependency_graph
from app.services.code_analysis.parsers import get_parser_for_file

router = APIRouter(tags=["Code Intelligence"])


@router.post("/api/code-analysis/repositories/{repository_id}/analyze", response_model=AnalysisRunResponse)
def run_repository_analysis(
    repository_id: str,
    payload: Optional[AnalyzeRepositoryRequest] = None,
    db: Session = Depends(get_db),
    _: object = Depends(require_engineer),
) -> AnalysisRunResponse:
    """Triggers code analysis for a repository from a local path."""
    repository = db.query(Repository).filter(Repository.id == repository_id).first()
    if not repository:
        raise HTTPException(status_code=404, detail=f"Repository '{repository_id}' not found")

    target_path = payload.path if payload else None
    try:
        run = analyze_repository(db, repository_id=repository_id, target_path=target_path)
        return AnalysisRunResponse.model_validate(run)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/api/code-analysis/repositories/{repository_id}/files", response_model=List[CodeFileResponse])
def list_analyzed_files(
    repository_id: str,
    db: Session = Depends(get_db),
) -> List[CodeFileResponse]:
    """Returns analyzed code files for a repository."""
    files = db.query(CodeFile).filter(CodeFile.repository_id == repository_id).order_by(CodeFile.path.asc()).all()
    return [CodeFileResponse.model_validate(f) for f in files]


@router.get("/api/code-analysis/repositories/{repository_id}/entities", response_model=List[CodeEntityResponse])
def list_code_entities(
    repository_id: str,
    entity_type: Optional[str] = Query(None, description="Filter by entity type (FILE, CLASS, FUNCTION, METHOD)"),
    file_id: Optional[str] = Query(None, description="Filter by code file ID"),
    name: Optional[str] = Query(None, description="Filter by entity name"),
    db: Session = Depends(get_db),
) -> List[CodeEntityResponse]:
    """Returns extracted code entities for a repository with optional filtering."""
    query = db.query(CodeEntity).filter(CodeEntity.repository_id == repository_id)
    if entity_type:
        query = query.filter(CodeEntity.entity_type == entity_type.upper())
    if file_id:
        query = query.filter(CodeEntity.file_id == file_id)
    if name:
        query = query.filter(CodeEntity.name.ilike(f"%{name}%"))

    entities = query.order_by(CodeEntity.start_line.asc()).all()
    return [CodeEntityResponse.model_validate(e) for e in entities]


@router.get("/api/code-analysis/repositories/{repository_id}/relationships", response_model=List[CodeRelationshipResponse])
def list_code_relationships(
    repository_id: str,
    relationship_type: Optional[str] = Query(None, description="Filter by relationship type (CONTAINS, IMPORTS, CALLS)"),
    source_entity_id: Optional[str] = Query(None, description="Filter by source entity ID"),
    target_entity_id: Optional[str] = Query(None, description="Filter by target entity ID"),
    db: Session = Depends(get_db),
) -> List[CodeRelationshipResponse]:
    """Returns code relationships for a repository with optional filtering."""
    query = db.query(CodeRelationship).filter(CodeRelationship.repository_id == repository_id)
    if relationship_type:
        query = query.filter(CodeRelationship.relationship_type == relationship_type.upper())
    if source_entity_id:
        query = query.filter(CodeRelationship.source_entity_id == source_entity_id)
    if target_entity_id:
        query = query.filter(CodeRelationship.target_entity_id == target_entity_id)

    rels = query.all()
    return [CodeRelationshipResponse.model_validate(r) for r in rels]


@router.get("/api/code-analysis/repositories/{repository_id}/graph", response_model=GraphResponse)
def get_repository_dependency_graph(
    repository_id: str,
    db: Session = Depends(get_db),
) -> GraphResponse:
    """Returns graph representation containing nodes and edges for dependency visualization."""
    return build_dependency_graph(db, repository_id=repository_id)


@router.get("/api/code-analysis/runs/{run_id}", response_model=AnalysisRunResponse)
def get_analysis_run(
    run_id: str,
    db: Session = Depends(get_db),
) -> AnalysisRunResponse:
    """Returns analysis run status and statistics."""
    run = db.query(AnalysisRun).filter(AnalysisRun.id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail=f"Analysis run '{run_id}' not found")
    return AnalysisRunResponse.model_validate(run)


# Compatibility endpoints for simple in-memory analysis testing
@router.post("/api/analysis/run")
def legacy_run_single_source_analysis(payload: dict, _: object = Depends(require_engineer)) -> dict:
    """Legacy compatibility route for parsing single raw source snippet directly."""
    language = payload.get("language", "python")
    source = payload.get("source", "")
    file_path = payload.get("file_path", "example.py")

    parser = get_parser_for_file(file_path, language)
    parse_result = parser.parse(file_path, source.encode("utf-8"))

    entities_data = [
        {"name": e.name, "type": e.entity_type, "start_line": e.start_line, "end_line": e.end_line}
        for e in parse_result.entities
    ]
    imports_data = [
        {"module": i.module, "items": i.imported_items, "line": i.start_line}
        for i in parse_result.imports
    ]
    calls_data = [
        {"callee": c.callee, "caller": c.caller_scope, "line": c.start_line}
        for c in parse_result.calls
    ]
    edges = [
        {"source": c.caller_scope.split(":")[-1] if c.caller_scope else "file", "target": c.callee, "type": "CALLS"}
        for c in parse_result.calls
    ]

    return {
        "file_path": file_path,
        "language": language,
        "entities": entities_data,
        "imports": imports_data,
        "calls": calls_data,
        "dependency_graph": edges,
    }


@router.get("/api/analysis/runs")
def legacy_list_analysis_runs(db: Session = Depends(get_db)) -> List[AnalysisRunResponse]:
    """Legacy compatibility route for listing all analysis runs."""
    runs = db.query(AnalysisRun).order_by(AnalysisRun.started_at.desc()).all()
    return [AnalysisRunResponse.model_validate(r) for r in runs]
