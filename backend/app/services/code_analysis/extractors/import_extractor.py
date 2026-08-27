import os
from typing import Dict, List, Optional
from uuid import uuid4

from app.models.code_entity import CodeEntity
from app.models.code_relationship import CodeRelationship
from app.services.code_analysis.parsers.base import ParsedImport


def resolve_import_path(
    source_file_path: str,
    import_module: str,
    all_file_paths: List[str],
) -> Optional[str]:
    """Resolves an import module string to a relative repository file path.
    
    Supports:
    - Relative imports: './auth', '../services/user'
    - Package/module level imports: 'auth', 'database'
    """
    clean_mod = import_module.strip()
    source_dir = os.path.dirname(source_file_path)

    # Normalize relative imports
    if clean_mod.startswith("."):
        target_path_norm = os.path.normpath(os.path.join(source_dir, clean_mod)).replace("\\", "/")
    else:
        target_path_norm = clean_mod.replace(".", "/").replace("\\", "/")

    # Candidate extension variations
    candidates = [
        target_path_norm,
        f"{target_path_norm}.py",
        f"{target_path_norm}.ts",
        f"{target_path_norm}.tsx",
        f"{target_path_norm}.js",
        f"{target_path_norm}.jsx",
        f"{target_path_norm}/index.ts",
        f"{target_path_norm}/index.tsx",
        f"{target_path_norm}/index.js",
        f"{target_path_norm}/index.jsx",
        f"{target_path_norm}/__init__.py",
    ]

    path_set = set(all_file_paths)
    for cand in candidates:
        if cand in path_set:
            return cand

    # Fallback partial matching
    for path in all_file_paths:
        if path.endswith(f"/{target_path_norm}.py") or path.endswith(f"/{target_path_norm}.ts") or path.endswith(f"/{target_path_norm}.js"):
            return path

    return None


def extract_import_relationships(
    repository_id: str,
    file_entity_map: Dict[str, CodeEntity],  # file_path -> FILE CodeEntity
    file_imports_map: Dict[str, List[ParsedImport]],  # file_path -> List[ParsedImport]
) -> List[CodeRelationship]:
    """Extracts IMPORTS relationships between file entities."""
    relationships: List[CodeRelationship] = []
    all_file_paths = list(file_entity_map.keys())

    for source_file_path, parsed_imports in file_imports_map.items():
        source_file_entity = file_entity_map.get(source_file_path)
        if not source_file_entity:
            continue

        seen_targets = set()
        for imp in parsed_imports:
            target_path = resolve_import_path(source_file_path, imp.module, all_file_paths)
            target_file_entity = file_entity_map.get(target_path) if target_path else None

            target_entity_id = target_file_entity.id if target_file_entity else None
            resolved = target_file_entity is not None

            key = (source_file_entity.id, target_entity_id or imp.module)
            if key in seen_targets:
                continue
            seen_targets.add(key)

            rel = CodeRelationship(
                id=str(uuid4()),
                repository_id=repository_id,
                source_entity_id=source_file_entity.id,
                target_entity_id=target_entity_id,
                relationship_type="IMPORTS",
                resolved=resolved,
                raw_target=imp.module,
            )
            relationships.append(rel)

    return relationships
