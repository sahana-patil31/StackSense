from typing import List, Optional
import tree_sitter
import tree_sitter_python

from app.services.code_analysis.parsers.base import (
    BaseParser,
    ParsedCall,
    ParsedEntity,
    ParsedImport,
    ParseResult,
)


class PythonParser(BaseParser):
    def __init__(self):
        self.language = tree_sitter.Language(tree_sitter_python.language())

    def parse(self, file_path: str, source_code: bytes) -> ParseResult:
        parser = tree_sitter.Parser(self.language)
        tree = parser.parse(source_code)
        
        has_error = tree.root_node.has_error
        errors: List[str] = []
        if has_error:
            errors.append("Syntax error or partial parsing encountered in Python source file")

        entities: List[ParsedEntity] = []
        imports: List[ParsedImport] = []
        calls: List[ParsedCall] = []

        def get_node_text(node) -> str:
            return source_code[node.start_byte:node.end_byte].decode("utf-8", errors="replace")

        def traverse(node, current_scope: Optional[str] = None):
            node_type = node.type

            if node_type == "class_definition":
                name_node = node.child_by_field_name("name")
                name = get_node_text(name_node) if name_node else "AnonymousClass"
                start_line = node.start_point[0] + 1
                end_line = node.end_point[0] + 1
                
                entities.append(
                    ParsedEntity(
                        name=name,
                        entity_type="CLASS",
                        start_line=start_line,
                        end_line=end_line,
                        parent_scope=current_scope,
                    )
                )
                
                new_scope = f"class:{name}"
                body_node = node.child_by_field_name("body")
                children_to_visit = body_node.children if body_node else node.children
                for child in children_to_visit:
                    traverse(child, new_scope)
                return

            elif node_type in ("function_definition", "async_function_definition"):
                name_node = node.child_by_field_name("name")
                name = get_node_text(name_node) if name_node else "anonymous"
                start_line = node.start_point[0] + 1
                end_line = node.end_point[0] + 1
                
                entity_type = "METHOD" if current_scope and current_scope.startswith("class:") else "FUNCTION"
                entities.append(
                    ParsedEntity(
                        name=name,
                        entity_type=entity_type,
                        start_line=start_line,
                        end_line=end_line,
                        parent_scope=current_scope,
                    )
                )

                new_scope = f"function:{name}"
                body_node = node.child_by_field_name("body")
                children_to_visit = body_node.children if body_node else node.children
                for child in children_to_visit:
                    traverse(child, new_scope)
                return

            elif node_type == "import_statement":
                # e.g., import os, sys
                line = node.start_point[0] + 1
                for child in node.children:
                    if child.type == "dotted_name":
                        mod_name = get_node_text(child)
                        imports.append(ParsedImport(module=mod_name, is_relative=False, start_line=line))
                    elif child.type == "aliased_import":
                        name_n = child.child_by_field_name("name")
                        if name_n:
                            imports.append(ParsedImport(module=get_node_text(name_n), is_relative=False, start_line=line))

            elif node_type == "import_from_statement":
                # e.g., from auth import validate_token
                line = node.start_point[0] + 1
                module_node = node.child_by_field_name("module_name") or node.child_by_field_name("module")
                
                # Check for relative dot indicators
                dots = ""
                for child in node.children:
                    if child.type in (".", "relative_import"):
                        dots += get_node_text(child)
                
                mod_name = get_node_text(module_node) if module_node else ""
                full_mod = dots + mod_name if dots else mod_name
                is_relative = len(dots) > 0 or mod_name.startswith(".")

                imported_names = []
                for child in node.children:
                    if child.type == "dotted_name" and child != module_node:
                        imported_names.append(get_node_text(child))
                    elif child.type == "import_list":
                        for sub in child.children:
                            if sub.type in ("identifier", "dotted_name"):
                                imported_names.append(get_node_text(sub))

                if full_mod:
                    imports.append(
                        ParsedImport(
                            module=full_mod,
                            imported_items=imported_names,
                            is_relative=is_relative,
                            start_line=line,
                        )
                    )

            elif node_type == "call":
                func_node = node.child_by_field_name("function")
                if func_node:
                    callee_text = get_node_text(func_node)
                    calls.append(
                        ParsedCall(
                            callee=callee_text,
                            caller_scope=current_scope,
                            start_line=node.start_point[0] + 1,
                        )
                    )

            for child in node.children:
                traverse(child, current_scope)

        traverse(tree.root_node)

        return ParseResult(
            file_path=file_path,
            language="python",
            status="error" if (has_error and not entities and not imports) else "success",
            errors=errors,
            entities=entities,
            imports=imports,
            calls=calls,
        )
