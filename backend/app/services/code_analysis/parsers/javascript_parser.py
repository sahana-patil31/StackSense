from typing import List, Optional
import tree_sitter
import tree_sitter_javascript

from app.services.code_analysis.parsers.base import (
    BaseParser,
    ParsedCall,
    ParsedEntity,
    ParsedImport,
    ParseResult,
)


class JavaScriptParser(BaseParser):
    def __init__(self):
        self.language = tree_sitter.Language(tree_sitter_javascript.language())

    def parse(self, file_path: str, source_code: bytes) -> ParseResult:
        parser = tree_sitter.Parser(self.language)
        tree = parser.parse(source_code)
        
        has_error = tree.root_node.has_error
        errors: List[str] = []
        if has_error:
            errors.append("Syntax error or partial parsing encountered in JavaScript source file")

        entities: List[ParsedEntity] = []
        imports: List[ParsedImport] = []
        calls: List[ParsedCall] = []

        def get_node_text(node) -> str:
            return source_code[node.start_byte:node.end_byte].decode("utf-8", errors="replace")

        def traverse(node, current_scope: Optional[str] = None):
            node_type = node.type

            if node_type in ("class_declaration", "class"):
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

            elif node_type == "method_definition":
                name_node = node.child_by_field_name("name")
                name = get_node_text(name_node) if name_node else "anonymous"
                start_line = node.start_point[0] + 1
                end_line = node.end_point[0] + 1

                entities.append(
                    ParsedEntity(
                        name=name,
                        entity_type="METHOD",
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

            elif node_type == "function_declaration":
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

            elif node_type in ("variable_declarator", "lexical_declaration"):
                # Handle const foo = () => {} or const foo = function() {}
                if node_type == "variable_declarator":
                    name_node = node.child_by_field_name("name")
                    value_node = node.child_by_field_name("value")
                    if name_node and value_node and value_node.type in ("arrow_function", "function_expression", "function"):
                        func_name = get_node_text(name_node)
                        start_line = node.start_point[0] + 1
                        end_line = node.end_point[0] + 1

                        entity_type = "METHOD" if current_scope and current_scope.startswith("class:") else "FUNCTION"
                        entities.append(
                            ParsedEntity(
                                name=func_name,
                                entity_type=entity_type,
                                start_line=start_line,
                                end_line=end_line,
                                parent_scope=current_scope,
                            )
                        )

                        new_scope = f"function:{func_name}"
                        for child in value_node.children:
                            traverse(child, new_scope)
                        return

            elif node_type == "import_statement":
                # e.g., import { foo } from './bar'
                line = node.start_point[0] + 1
                source_node = node.child_by_field_name("source")
                mod_path = get_node_text(source_node).strip("'\"") if source_node else ""

                imported_names = []
                import_clause = node.child_by_field_name("import") or node
                for child in import_clause.children:
                    if child.type == "import_clause":
                        for sub in child.children:
                            if sub.type in ("identifier", "named_imports"):
                                if sub.type == "identifier":
                                    imported_names.append(get_node_text(sub))
                                else:
                                    for spec in sub.children:
                                        if spec.type == "import_specifier":
                                            n = spec.child_by_field_name("name") or spec
                                            imported_names.append(get_node_text(n))

                if mod_path:
                    imports.append(
                        ParsedImport(
                            module=mod_path,
                            imported_items=imported_names,
                            is_relative=mod_path.startswith("."),
                            start_line=line,
                        )
                    )

            elif node_type == "call_expression":
                func_node = node.child_by_field_name("function")
                if func_node:
                    callee_text = get_node_text(func_node)
                    line = node.start_point[0] + 1

                    # Check if require('module')
                    if callee_text == "require":
                        args_node = node.child_by_field_name("arguments")
                        if args_node and args_node.children:
                            for arg in args_node.children:
                                if arg.type in ("string", "string_fragment"):
                                    mod_path = get_node_text(arg).strip("'\"")
                                    if mod_path:
                                        imports.append(
                                            ParsedImport(
                                                module=mod_path,
                                                imported_items=[],
                                                is_relative=mod_path.startswith("."),
                                                start_line=line,
                                            )
                                        )
                    else:
                        calls.append(
                            ParsedCall(
                                callee=callee_text,
                                caller_scope=current_scope,
                                start_line=line,
                            )
                        )

            for child in node.children:
                traverse(child, current_scope)

        traverse(tree.root_node)

        return ParseResult(
            file_path=file_path,
            language="javascript",
            status="error" if (has_error and not entities and not imports) else "success",
            errors=errors,
            entities=entities,
            imports=imports,
            calls=calls,
        )
