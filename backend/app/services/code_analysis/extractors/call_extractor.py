from typing import Dict, List
from uuid import uuid4

from app.models.code_entity import CodeEntity
from app.models.code_relationship import CodeRelationship
from app.services.code_analysis.parsers.base import ParsedCall


def extract_call_relationships(
    repository_id: str,
    all_entities: List[CodeEntity],
    file_calls_map: Dict[str, List[ParsedCall]],  # file_path -> List[ParsedCall]
) -> List[CodeRelationship]:
    """Extracts CALLS relationships between functions/methods."""
    relationships: List[CodeRelationship] = []

    # Map file_id -> list of CodeEntity in that file
    file_id_to_entities: Dict[str, List[CodeEntity]] = {}
    # Map name -> list of CodeEntity across entire repository
    name_to_entities: Dict[str, List[CodeEntity]] = {}
    # Map entity ID -> CodeEntity
    entity_by_id: Dict[str, CodeEntity] = {}

    for entity in all_entities:
        entity_by_id[entity.id] = entity
        file_id_to_entities.setdefault(entity.file_id, []).append(entity)
        if entity.entity_type in ("FUNCTION", "METHOD"):
            name_to_entities.setdefault(entity.name, []).append(entity)

    # Map file_path to file CodeEntity
    path_to_file_entity: Dict[str, CodeEntity] = {
        e.qualified_name: e for e in all_entities if e.entity_type == "FILE" and e.qualified_name
    }

    for file_path, calls in file_calls_map.items():
        file_entity = path_to_file_entity.get(file_path)
        if not file_entity:
            continue

        file_entities = file_id_to_entities.get(file_entity.id, [])

        for call in calls:
            # 1. Determine caller entity
            caller_entity = None
            if call.caller_scope:
                caller_name = call.caller_scope.split(":")[-1]
                for candidate in file_entities:
                    if candidate.name == caller_name and candidate.entity_type in ("FUNCTION", "METHOD"):
                        caller_entity = candidate
                        break

            if not caller_entity:
                # Default caller entity to file entity if outside function scope
                caller_entity = file_entity

            # 2. Extract base callee name (e.g. 'validate_token()' -> 'validate_token', 'service.charge()' -> 'charge')
            raw_callee = call.callee.strip()
            callee_name = raw_callee.split(".")[-1].split("(")[0].strip()

            # 3. Resolve target entity
            target_entity = None
            
            # Check 3a: Local function/method in same file
            for candidate in file_entities:
                if candidate.name == callee_name and candidate.entity_type in ("FUNCTION", "METHOD"):
                    target_entity = candidate
                    break

            # Check 3b: Unique function/method matching callee_name across repository
            if not target_entity:
                global_matches = name_to_entities.get(callee_name, [])
                if len(global_matches) == 1:
                    target_entity = global_matches[0]

            resolved = target_entity is not None
            target_id = target_entity.id if target_entity else None

            rel = CodeRelationship(
                id=str(uuid4()),
                repository_id=repository_id,
                source_entity_id=caller_entity.id,
                target_entity_id=target_id,
                relationship_type="CALLS",
                resolved=resolved,
                raw_target=raw_callee,
            )
            relationships.append(rel)

    return relationships
