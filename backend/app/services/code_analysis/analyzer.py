import os
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Optional
from uuid import uuid4

from sqlalchemy.orm import Session

from app.models.analysis_run import AnalysisRun
from app.models.code_entity import CodeEntity
from app.models.code_file import CodeFile
from app.models.code_relationship import CodeRelationship
from app.models.repository import Repository
from app.core.config import get_settings
from app.services.code_analysis.extractors import (
    extract_call_relationships,
    extract_entities_for_file,
    extract_import_relationships,
)
from app.services.code_analysis.parsers import get_parser_for_file
from app.services.code_analysis.parsers.base import ParsedCall, ParsedImport
from app.services.code_analysis.repository_scanner import RepositoryScanner


def analyze_repository(
    db: Session,
    repository_id: str,
    target_path: Optional[str] = None,
) -> AnalysisRun:
    """Orchestrates code analysis for a repository from a local filesystem directory.
    
    Creates an AnalysisRun, discovers source files, parses ASTs using Tree-sitter,
    extracts entities & relationships, replaces outdated analysis records, and stores metrics.
    """
    repository = db.query(Repository).filter(Repository.id == repository_id).first()
    if not repository:
        raise ValueError(f"Repository with ID '{repository_id}' not found.")

    # Determine local directory path
    local_dir = target_path or repository.url or os.getcwd()
    if target_path:
        if ".." in Path(target_path).parts:
            raise ValueError("Analysis path cannot contain traversal segments")
        requested = Path(target_path).expanduser().resolve()
        allowed_root = get_settings().code_analysis_allowed_root
        if allowed_root:
            root = Path(allowed_root).expanduser().resolve()
            if requested != root and root not in requested.parents:
                raise ValueError("Analysis path is outside the configured allowed root")
        local_dir = str(requested)
    if not os.path.exists(local_dir):
        # Fallback to current working directory if path is not a local folder
        local_dir = os.getcwd()

    run_id = str(uuid4())
    run = AnalysisRun(
        id=run_id,
        repository_id=repository_id,
        status="running",
        files_discovered=0,
        files_analyzed=0,
        entities_found=0,
        relationships_found=0,
        files_failed=0,
        started_at=datetime.now(timezone.utc),
    )
    db.add(run)
    db.commit()
    db.refresh(run)

    try:
        scanner = RepositoryScanner()
        discovered_files = scanner.scan(local_dir)
        run.files_discovered = len(discovered_files)

        new_code_files: List[CodeFile] = []
        all_entities: List[CodeEntity] = []
        file_entity_map: Dict[str, CodeEntity] = {}
        file_imports_map: Dict[str, List[ParsedImport]] = {}
        file_calls_map: Dict[str, List[ParsedCall]] = {}

        analyzed_count = 0
        failed_count = 0

        all_contains_rels: List[CodeRelationship] = []

        for disc in discovered_files:
            file_id = str(uuid4())
            try:
                with open(disc.absolute_path, "rb") as f:
                    source_bytes = f.read()

                line_count = source_bytes.count(b"\n") + 1
                parser = get_parser_for_file(disc.relative_path, disc.language)
                parse_result = parser.parse(disc.relative_path, source_bytes)

                code_file = CodeFile(
                    id=file_id,
                    repository_id=repository_id,
                    path=disc.relative_path,
                    language=disc.language,
                    size=disc.size,
                    analysis_status=parse_result.status,
                    analysis_error="; ".join(parse_result.errors) if parse_result.errors else None,
                    analyzed_at=datetime.now(timezone.utc),
                )
                new_code_files.append(code_file)

                # Extract entities & CONTAINS relationships for file
                file_entities, contains_rels = extract_entities_for_file(
                    repository_id=repository_id,
                    file_id=file_id,
                    file_path=disc.relative_path,
                    parsed_entities=parse_result.entities,
                    line_count=line_count,
                )
                all_entities.extend(file_entities)
                all_contains_rels.extend(contains_rels)

                # Store file top-level entity mapping
                file_entity = file_entities[0]  # FILE entity is first
                file_entity_map[disc.relative_path] = file_entity

                # Accumulate imports & calls for cross-file relationship resolution
                file_imports_map[disc.relative_path] = parse_result.imports
                file_calls_map[disc.relative_path] = parse_result.calls

                if parse_result.status == "error":
                    failed_count += 1
                else:
                    analyzed_count += 1

            except Exception as exc:
                failed_count += 1
                code_file = CodeFile(
                    id=file_id,
                    repository_id=repository_id,
                    path=disc.relative_path,
                    language=disc.language,
                    size=disc.size,
                    analysis_status="error",
                    analysis_error=str(exc),
                    analyzed_at=datetime.now(timezone.utc),
                )
                new_code_files.append(code_file)

        # Extract IMPORTS and CALLS relationships across all files
        import_rels = extract_import_relationships(
            repository_id=repository_id,
            file_entity_map=file_entity_map,
            file_imports_map=file_imports_map,
        )

        call_rels = extract_call_relationships(
            repository_id=repository_id,
            all_entities=all_entities,
            file_calls_map=file_calls_map,
        )

        all_relationships = all_contains_rels + import_rels + call_rels

        # Re-Analysis Strategy: Replace existing analysis records for this repository
        db.query(CodeRelationship).filter(CodeRelationship.repository_id == repository_id).delete(synchronize_session=False)
        db.query(CodeEntity).filter(CodeEntity.repository_id == repository_id).delete(synchronize_session=False)
        db.query(CodeFile).filter(CodeFile.repository_id == repository_id).delete(synchronize_session=False)
        db.flush()

        # Insert new analysis records
        db.bulk_save_objects(new_code_files)
        db.bulk_save_objects(all_entities)
        db.bulk_save_objects(all_relationships)

        # Update analysis run metrics
        run.files_analyzed = analyzed_count
        run.files_failed = failed_count
        run.entities_found = len(all_entities)
        run.relationships_found = len(all_relationships)
        run.status = "completed" if failed_count == 0 else ("partial" if analyzed_count > 0 else "failed")
        run.completed_at = datetime.now(timezone.utc)

        db.commit()
        db.refresh(run)
        return run

    except Exception as exc:
        db.rollback()
        run.status = "failed"
        run.error_summary = str(exc)
        run.completed_at = datetime.now(timezone.utc)
        db.add(run)
        db.commit()
        db.refresh(run)
        return run
