from typing import List, Optional
from sqlalchemy.orm import Session

from app.models.code_entity import CodeEntity
from app.models.code_file import CodeFile
from app.models.code_relationship import CodeRelationship
from app.schemas.code_analysis import GraphEdge, GraphNode, GraphResponse


def build_dependency_graph(db: Session, repository_id: str) -> GraphResponse:
    """Builds node & edge dependency graph representation for a repository."""
    files: List[CodeFile] = db.query(CodeFile).filter(CodeFile.repository_id == repository_id).all()
    entities: List[CodeEntity] = db.query(CodeEntity).filter(CodeEntity.repository_id == repository_id).all()
    relationships: List[CodeRelationship] = db.query(CodeRelationship).filter(CodeRelationship.repository_id == repository_id).all()

    file_map = {f.id: f.path for f in files}

    nodes: List[GraphNode] = []
    node_id_set = set()

    for entity in entities:
        node = GraphNode(
            id=entity.id,
            label=entity.name,
            type=entity.entity_type,
            file_id=entity.file_id,
            file_path=file_map.get(entity.file_id),
            name=entity.name,
            qualified_name=entity.qualified_name,
            start_line=entity.start_line,
            end_line=entity.end_line,
        )
        nodes.append(node)
        node_id_set.add(entity.id)

    edges: List[GraphEdge] = []
    for rel in relationships:
        # Include edges if source exists in graph, and target exists or is unresolved
        if rel.source_entity_id in node_id_set:
            target_id = rel.target_entity_id if (rel.target_entity_id and rel.target_entity_id in node_id_set) else (rel.raw_target or "unresolved")
            edge = GraphEdge(
                id=rel.id,
                source=rel.source_entity_id,
                target=target_id,
                relationship_type=rel.relationship_type,
                resolved=rel.resolved,
                raw_target=rel.raw_target,
            )
            edges.append(edge)

    return GraphResponse(nodes=nodes, edges=edges)
