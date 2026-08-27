from typing import Dict, List, Tuple
from uuid import uuid4

from app.models.code_entity import CodeEntity
from app.models.code_relationship import CodeRelationship
from app.services.code_analysis.parsers.base import ParsedEntity


def extract_entities_for_file(
    repository_id: str,
    file_id: str,
    file_path: str,
    parsed_entities: List[ParsedEntity],
    line_count: int = 1,
) -> Tuple[List[CodeEntity], List[CodeRelationship]]:
    """Extracts CodeEntity records and CONTAINS relationships for a single file.
    
    Creates:
    - Top-level FILE entity representing the file itself.
    - Child entities (CLASS, FUNCTION, METHOD) with parent_entity_id links.
    - CONTAINS relationships connecting parent entities to child entities.
    """
    entities: List[CodeEntity] = []
    relationships: List[CodeRelationship] = []

    # 1. Create FILE entity
    file_entity = CodeEntity(
        id=str(uuid4()),
        repository_id=repository_id,
        file_id=file_id,
        parent_entity_id=None,
        entity_type="FILE",
        name=file_path.split("/")[-1],
        qualified_name=file_path,
        start_line=1,
        end_line=max(1, line_count),
    )
    entities.append(file_entity)

    # Scope mapping: e.g. "class:PaymentService" -> entity.id
    scope_to_entity_id: Dict[str, str] = {}
    
    for parsed in parsed_entities:
        parent_id = file_entity.id
        if parsed.parent_scope and parsed.parent_scope in scope_to_entity_id:
            parent_id = scope_to_entity_id[parsed.parent_scope]

        qualified_name = f"{file_path}::{parsed.name}"
        if parsed.parent_scope:
            scope_name = parsed.parent_scope.split(":")[-1]
            qualified_name = f"{file_path}::{scope_name}::{parsed.name}"

        entity = CodeEntity(
            id=str(uuid4()),
            repository_id=repository_id,
            file_id=file_id,
            parent_entity_id=parent_id,
            entity_type=parsed.entity_type,
            name=parsed.name,
            qualified_name=qualified_name,
            start_line=parsed.start_line,
            end_line=parsed.end_line,
        )
        entities.append(entity)

        # Track scope ID for nested entities (methods inside class, etc.)
        if parsed.entity_type == "CLASS":
            scope_to_entity_id[f"class:{parsed.name}"] = entity.id
        elif parsed.entity_type in ("FUNCTION", "METHOD"):
            scope_to_entity_id[f"function:{parsed.name}"] = entity.id

        # CONTAINS relationship
        rel = CodeRelationship(
            id=str(uuid4()),
            repository_id=repository_id,
            source_entity_id=parent_id,
            target_entity_id=entity.id,
            relationship_type="CONTAINS",
            resolved=True,
            raw_target=entity.name,
        )
        relationships.append(rel)

    return entities, relationships
