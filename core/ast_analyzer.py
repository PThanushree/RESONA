"""
RESONA AST Analyzer Module
Extracts structural code hierarchy, AST trees, scope nesting, variable scopes, and navigability maps.
Designed for non-visual code comprehension under KSCST Project Guidelines (Objective 2).
"""

from __future__ import annotations
import ast
import inspect
from dataclasses import dataclass, field, asdict
from typing import List, Optional, Dict, Any, Union, Set


@dataclass
class ScopeInfo:
    """Represents a lexical variable scope (global, function, class, comprehension)."""
    scope_id: str
    scope_type: str  # 'global', 'function', 'class', 'comprehension'
    name: str
    start_line: int
    end_line: int
    parent_scope_id: Optional[str] = None
    variables_defined: List[str] = field(default_factory=list)
    variables_read: List[str] = field(default_factory=list)
    parameters: List[str] = field(default_factory=list)
    global_declarations: List[str] = field(default_factory=list)
    nonlocal_declarations: List[str] = field(default_factory=list)
    shadowed_variables: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class CodeNode:
    """Represents a structural block in the AST hierarchy."""
    id: str
    node_type: str
    name: str
    start_line: int
    end_line: int
    col_offset: int
    nesting_level: int
    summary: str
    description: str
    children: List[CodeNode] = field(default_factory=list)
    parent_id: Optional[str] = None
    parameters: List[str] = field(default_factory=list)
    variables_assigned: List[str] = field(default_factory=list)
    calls: List[str] = field(default_factory=list)
    complexity: int = 1
    scope_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert node to recursive dictionary representation."""
        data = asdict(self)
        return data


@dataclass
class SyntaxErrorInfo:
    """Represents syntax or indentation error information with accessible guidance."""
    line: int
    column: int
    error_type: str
    message: str
    text: str
    spoken_advice: str


@dataclass
class CodeAnalysisResult:
    """Complete structural analysis output for source code."""
    is_valid: bool
    root_node: Optional[CodeNode]
    flattened_nodes: List[CodeNode]
    syntax_error: Optional[SyntaxErrorInfo] = None
    total_lines: int = 0
    total_functions: int = 0
    total_classes: int = 0
    total_loops: int = 0
    total_branches: int = 0
    max_nesting_depth: int = 0
    audio_landmarks: List[Dict[str, Any]] = field(default_factory=list)
    variable_scopes: List[ScopeInfo] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "is_valid": self.is_valid,
            "root_node": self.root_node.to_dict() if self.root_node else None,
            "flattened_nodes": [n.to_dict() for n in self.flattened_nodes],
            "syntax_error": asdict(self.syntax_error) if self.syntax_error else None,
            "total_lines": self.total_lines,
            "total_functions": self.total_functions,
            "total_classes": self.total_classes,
            "total_loops": self.total_loops,
            "total_branches": self.total_branches,
            "max_nesting_depth": self.max_nesting_depth,
            "audio_landmarks": self.audio_landmarks,
            "variable_scopes": [s.to_dict() for s in self.variable_scopes]
        }


class ScopeVisitor(ast.NodeVisitor):
    """Extracts lexical scope boundaries, variable declarations, and shadowing."""

    def __init__(self, total_lines: int):
        self.scopes: List[ScopeInfo] = []
        self.scope_stack: List[ScopeInfo] = []
        self.scope_counter = 0

        # Create root global scope
        root_scope = ScopeInfo(
            scope_id="scope_global",
            scope_type="global",
            name="global",
            start_line=1,
            end_line=max(total_lines, 1)
        )
        self.scopes.append(root_scope)
        self.scope_stack.append(root_scope)

    def _next_scope_id(self, prefix: str) -> str:
        self.scope_counter += 1
        return f"scope_{prefix}_{self.scope_counter}"

    def visit_FunctionDef(self, node: ast.FunctionDef):
        self._handle_function_scope(node, "function")

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        self._handle_function_scope(node, "async_function")

    def visit_ClassDef(self, node: ast.ClassDef):
        parent_scope = self.scope_stack[-1]
        scope_id = self._next_scope_id(f"class_{node.name}")
        scope = ScopeInfo(
            scope_id=scope_id,
            scope_type="class",
            name=node.name,
            start_line=node.lineno,
            end_line=getattr(node, "end_lineno", node.lineno),
            parent_scope_id=parent_scope.scope_id
        )
        self.scopes.append(scope)
        self.scope_stack.append(scope)
        self.generic_visit(node)
        self.scope_stack.pop()

    def _handle_function_scope(self, node: Union[ast.FunctionDef, ast.AsyncFunctionDef], stype: str):
        parent_scope = self.scope_stack[-1]
        params = [a.arg for a in node.args.args]
        scope_id = self._next_scope_id(f"func_{node.name}")

        # Check for shadowing parent scope variables
        shadowed = []
        outer_vars = set(parent_scope.variables_defined).union(parent_scope.parameters)
        for p in params:
            if p in outer_vars:
                shadowed.append(p)

        scope = ScopeInfo(
            scope_id=scope_id,
            scope_type=stype,
            name=node.name,
            start_line=node.lineno,
            end_line=getattr(node, "end_lineno", node.lineno),
            parent_scope_id=parent_scope.scope_id,
            parameters=params,
            shadowed_variables=shadowed
        )
        # Register function name in parent scope
        if node.name not in parent_scope.variables_defined:
            parent_scope.variables_defined.append(node.name)

        self.scopes.append(scope)
        self.scope_stack.append(scope)
        self.generic_visit(node)
        self.scope_stack.pop()

    def visit_Name(self, node: ast.Name):
        curr_scope = self.scope_stack[-1]
        if isinstance(node.ctx, ast.Store):
            if node.id not in curr_scope.variables_defined and node.id not in curr_scope.parameters:
                curr_scope.variables_defined.append(node.id)
                # Check shadowing if in a nested function
                if len(self.scope_stack) > 1:
                    outer_scope = self.scope_stack[-2]
                    if node.id in outer_scope.variables_defined and node.id not in curr_scope.shadowed_variables:
                        curr_scope.shadowed_variables.append(node.id)
        elif isinstance(node.ctx, ast.Load):
            if node.id not in curr_scope.variables_read:
                curr_scope.variables_read.append(node.id)
        self.generic_visit(node)

    def visit_Global(self, node: ast.Global):
        curr_scope = self.scope_stack[-1]
        for name in node.names:
            if name not in curr_scope.global_declarations:
                curr_scope.global_declarations.append(name)
        self.generic_visit(node)

    def visit_Nonlocal(self, node: ast.Nonlocal):
        curr_scope = self.scope_stack[-1]
        for name in node.names:
            if name not in curr_scope.nonlocal_declarations:
                curr_scope.nonlocal_declarations.append(name)
        self.generic_visit(node)


class ASTAnalyzer:
    """
    Parses Python code and builds a non-visual navigable structural hierarchy
    with explicit variable scope modeling and audio landmark generation.
    """

    def __init__(self):
        self._counter = 0

    def analyze(self, source_code: str) -> CodeAnalysisResult:
        self._counter = 0
        lines = source_code.splitlines()
        total_lines = len(lines)

        try:
            tree = ast.parse(source_code)
        except SyntaxError as se:
            spoken = self._generate_syntax_advice(se, lines)
            err_info = SyntaxErrorInfo(
                line=se.lineno or 1,
                column=se.offset or 1,
                error_type=type(se).__name__,
                message=str(se.msg),
                text=se.text.strip() if se.text else "",
                spoken_advice=spoken
            )
            return CodeAnalysisResult(
                is_valid=False,
                root_node=None,
                flattened_nodes=[],
                syntax_error=err_info,
                total_lines=total_lines
            )

        # 1. Variable Scope Analysis
        scope_visitor = ScopeVisitor(total_lines)
        scope_visitor.visit(tree)
        scopes = scope_visitor.scopes

        # 2. Structural Node Tree
        root = CodeNode(
            id="node_0",
            node_type="Module",
            name="Module",
            start_line=1,
            end_line=max(total_lines, 1),
            col_offset=0,
            nesting_level=0,
            summary="Python Module",
            description=f"Python module containing {total_lines} lines",
            scope_id="scope_global"
        )

        flattened: List[CodeNode] = [root]
        landmarks: List[Dict[str, Any]] = []

        total_funcs = 0
        total_classes = 0
        total_loops = 0
        total_branches = 0
        max_depth = 0

        self._traverse_body(tree.body, root, flattened, depth=1)

        for node in flattened:
            if node.nesting_level > max_depth:
                max_depth = node.nesting_level

            if node.node_type in ("FunctionDef", "AsyncFunctionDef"):
                total_funcs += 1
                landmarks.append({
                    "id": node.id,
                    "line": node.start_line,
                    "type": "function",
                    "title": f"Function {node.name}",
                    "earcon": "function_entry",
                    "spoken": f"Function {node.name} at line {node.start_line}"
                })
            elif node.node_type == "ClassDef":
                total_classes += 1
                landmarks.append({
                    "id": node.id,
                    "line": node.start_line,
                    "type": "class",
                    "title": f"Class {node.name}",
                    "earcon": "class_entry",
                    "spoken": f"Class {node.name} at line {node.start_line}"
                })
            elif node.node_type in ("For", "While"):
                total_loops += 1
                landmarks.append({
                    "id": node.id,
                    "line": node.start_line,
                    "type": "loop",
                    "title": f"{node.node_type} loop",
                    "earcon": "loop_entry",
                    "spoken": f"{node.node_type} loop at line {node.start_line}, depth {node.nesting_level}"
                })
            elif node.node_type in ("If", "Elif", "Else"):
                total_branches += 1
                landmarks.append({
                    "id": node.id,
                    "line": node.start_line,
                    "type": "branch",
                    "title": node.summary,
                    "earcon": "branch_entry",
                    "spoken": f"{node.summary} at line {node.start_line}"
                })

        return CodeAnalysisResult(
            is_valid=True,
            root_node=root,
            flattened_nodes=flattened,
            syntax_error=None,
            total_lines=total_lines,
            total_functions=total_funcs,
            total_classes=total_classes,
            total_loops=total_loops,
            total_branches=total_branches,
            max_nesting_depth=max_depth,
            audio_landmarks=landmarks,
            variable_scopes=scopes
        )

    def _next_id(self) -> str:
        self._counter += 1
        return f"node_{self._counter}"

    def _traverse_body(self, stmts: List[ast.stmt], parent: CodeNode, flattened: List[CodeNode], depth: int):
        for stmt in stmts:
            node = self._create_code_node(stmt, depth, parent.id)
            if node:
                parent.children.append(node)
                flattened.append(node)

                if isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.For, ast.While, ast.With)):
                    self._traverse_body(stmt.body, node, flattened, depth + 1)
                elif isinstance(stmt, ast.If):
                    self._traverse_body(stmt.body, node, flattened, depth + 1)
                    if stmt.orelse:
                        if len(stmt.orelse) == 1 and isinstance(stmt.orelse[0], ast.If):
                            elif_node = self._create_elif_node(stmt.orelse[0], depth, parent.id)
                            parent.children.append(elif_node)
                            flattened.append(elif_node)
                            self._traverse_body(stmt.orelse[0].body, elif_node, flattened, depth + 1)
                            if stmt.orelse[0].orelse:
                                self._traverse_orelse(stmt.orelse[0].orelse, parent, flattened, depth)
                        else:
                            else_node = self._create_else_node(stmt.orelse, depth, parent.id)
                            parent.children.append(else_node)
                            flattened.append(else_node)
                            self._traverse_body(stmt.orelse, else_node, flattened, depth + 1)
                elif isinstance(stmt, ast.Try):
                    self._traverse_body(stmt.body, node, flattened, depth + 1)
                    for handler in stmt.handlers:
                        h_node = self._create_except_node(handler, depth, parent.id)
                        parent.children.append(h_node)
                        flattened.append(h_node)
                        self._traverse_body(handler.body, h_node, flattened, depth + 1)
                    if stmt.orelse:
                        self._traverse_body(stmt.orelse, node, flattened, depth + 1)
                    if stmt.finalbody:
                        finally_node = CodeNode(
                            id=self._next_id(),
                            node_type="Finally",
                            name="Finally block",
                            start_line=stmt.finalbody[0].lineno,
                            end_line=getattr(stmt.finalbody[-1], "end_lineno", stmt.finalbody[-1].lineno),
                            col_offset=stmt.finalbody[0].col_offset,
                            nesting_level=depth,
                            summary="Finally block",
                            description="Finally block that runs unconditionally",
                            parent_id=parent.id
                        )
                        parent.children.append(finally_node)
                        flattened.append(finally_node)
                        self._traverse_body(stmt.finalbody, finally_node, flattened, depth + 1)

    def _traverse_orelse(self, orelse: List[ast.stmt], parent: CodeNode, flattened: List[CodeNode], depth: int):
        if len(orelse) == 1 and isinstance(orelse[0], ast.If):
            elif_node = self._create_elif_node(orelse[0], depth, parent.id)
            parent.children.append(elif_node)
            flattened.append(elif_node)
            self._traverse_body(orelse[0].body, elif_node, flattened, depth + 1)
            if orelse[0].orelse:
                self._traverse_orelse(orelse[0].orelse, parent, flattened, depth)
        else:
            else_node = self._create_else_node(orelse, depth, parent.id)
            parent.children.append(else_node)
            flattened.append(else_node)
            self._traverse_body(orelse, else_node, flattened, depth + 1)

    def _create_code_node(self, stmt: ast.stmt, depth: int, parent_id: Optional[str]) -> Optional[CodeNode]:
        node_id = self._next_id()
        start = stmt.lineno
        end = getattr(stmt, "end_lineno", stmt.lineno)
        col = getattr(stmt, "col_offset", 0)

        if isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef)):
            is_async = isinstance(stmt, ast.AsyncFunctionDef)
            prefix = "Async function" if is_async else "Function"
            params = [a.arg for a in stmt.args.args]
            param_str = ", ".join(params) if params else "no parameters"
            summary = f"def {stmt.name}({', '.join(params)})"
            desc = f"{prefix} named {stmt.name} taking {param_str}, lines {start} to {end}"
            return CodeNode(
                id=node_id,
                node_type="AsyncFunctionDef" if is_async else "FunctionDef",
                name=stmt.name,
                start_line=start,
                end_line=end,
                col_offset=col,
                nesting_level=depth,
                summary=summary,
                description=desc,
                parent_id=parent_id,
                parameters=params
            )

        if isinstance(stmt, ast.ClassDef):
            bases = [ast.unparse(b) for b in stmt.bases]
            base_str = f" inheriting from {', '.join(bases)}" if bases else ""
            summary = f"class {stmt.name}"
            desc = f"Class named {stmt.name}{base_str}, lines {start} to {end}"
            return CodeNode(
                id=node_id,
                node_type="ClassDef",
                name=stmt.name,
                start_line=start,
                end_line=end,
                col_offset=col,
                nesting_level=depth,
                summary=summary,
                description=desc,
                parent_id=parent_id
            )

        if isinstance(stmt, ast.For):
            target = ast.unparse(stmt.target)
            iter_expr = ast.unparse(stmt.iter)
            summary = f"for {target} in {iter_expr}"
            desc = f"For loop iterating {target} over {iter_expr}, lines {start} to {end}"
            return CodeNode(
                id=node_id,
                node_type="For",
                name=f"for {target}",
                start_line=start,
                end_line=end,
                col_offset=col,
                nesting_level=depth,
                summary=summary,
                description=desc,
                parent_id=parent_id,
                variables_assigned=[target]
            )

        if isinstance(stmt, ast.While):
            test = ast.unparse(stmt.test)
            summary = f"while {test}"
            desc = f"While loop with condition {test}, lines {start} to {end}"
            return CodeNode(
                id=node_id,
                node_type="While",
                name=f"while {test}",
                start_line=start,
                end_line=end,
                col_offset=col,
                nesting_level=depth,
                summary=summary,
                description=desc,
                parent_id=parent_id
            )

        if isinstance(stmt, ast.If):
            test = ast.unparse(stmt.test)
            summary = f"if {test}"
            desc = f"Conditional if with test {test}, lines {start} to {end}"
            return CodeNode(
                id=node_id,
                node_type="If",
                name=f"if {test}",
                start_line=start,
                end_line=end,
                col_offset=col,
                nesting_level=depth,
                summary=summary,
                description=desc,
                parent_id=parent_id
            )

        if isinstance(stmt, ast.Try):
            return CodeNode(
                id=node_id,
                node_type="Try",
                name="try block",
                start_line=start,
                end_line=end,
                col_offset=col,
                nesting_level=depth,
                summary="try block",
                description=f"Try block guarding lines {start} to {end}",
                parent_id=parent_id
            )

        if isinstance(stmt, ast.With):
            items = [ast.unparse(item) for item in stmt.items]
            summary = f"with {', '.join(items)}"
            return CodeNode(
                id=node_id,
                node_type="With",
                name=summary,
                start_line=start,
                end_line=end,
                col_offset=col,
                nesting_level=depth,
                summary=summary,
                description=f"Context manager block {summary}, lines {start} to {end}",
                parent_id=parent_id
            )

        if isinstance(stmt, (ast.Assign, ast.AnnAssign, ast.AugAssign)):
            code_line = ast.unparse(stmt)
            targets = []
            if isinstance(stmt, ast.Assign):
                targets = [ast.unparse(t) for t in stmt.targets]
            elif isinstance(stmt, ast.AnnAssign):
                targets = [ast.unparse(stmt.target)]
            elif isinstance(stmt, ast.AugAssign):
                targets = [ast.unparse(stmt.target)]
            
            return CodeNode(
                id=node_id,
                node_type="Assign",
                name=f"assign: {', '.join(targets)}",
                start_line=start,
                end_line=end,
                col_offset=col,
                nesting_level=depth,
                summary=code_line,
                description=f"Assignment assigning to {', '.join(targets)} at line {start}",
                parent_id=parent_id,
                variables_assigned=targets
            )

        if isinstance(stmt, ast.Return):
            val = ast.unparse(stmt.value) if stmt.value else "None"
            return CodeNode(
                id=node_id,
                node_type="Return",
                name=f"return {val}",
                start_line=start,
                end_line=end,
                col_offset=col,
                nesting_level=depth,
                summary=f"return {val}",
                description=f"Return statement returning {val} at line {start}",
                parent_id=parent_id
            )

        if isinstance(stmt, ast.Expr):
            code_line = ast.unparse(stmt)
            return CodeNode(
                id=node_id,
                node_type="Expr",
                name=code_line[:30],
                start_line=start,
                end_line=end,
                col_offset=col,
                nesting_level=depth,
                summary=code_line,
                description=f"Expression {code_line} at line {start}",
                parent_id=parent_id
            )

        stmt_name = type(stmt).__name__
        code_line = ast.unparse(stmt)
        return CodeNode(
            id=node_id,
            node_type=stmt_name,
            name=stmt_name,
            start_line=start,
            end_line=end,
            col_offset=col,
            nesting_level=depth,
            summary=code_line,
            description=f"{stmt_name} statement at line {start}: {code_line}",
            parent_id=parent_id
        )

    def _create_elif_node(self, stmt: ast.If, depth: int, parent_id: Optional[str]) -> CodeNode:
        test = ast.unparse(stmt.test)
        start = stmt.lineno
        end = getattr(stmt, "end_lineno", stmt.lineno)
        return CodeNode(
            id=self._next_id(),
            node_type="Elif",
            name=f"elif {test}",
            start_line=start,
            end_line=end,
            col_offset=stmt.col_offset,
            nesting_level=depth,
            summary=f"elif {test}",
            description=f"Conditional elif with test {test}, lines {start} to {end}",
            parent_id=parent_id
        )

    def _create_else_node(self, orelse: List[ast.stmt], depth: int, parent_id: Optional[str]) -> CodeNode:
        start = orelse[0].lineno
        end = getattr(orelse[-1], "end_lineno", orelse[-1].lineno)
        return CodeNode(
            id=self._next_id(),
            node_type="Else",
            name="else block",
            start_line=start,
            end_line=end,
            col_offset=orelse[0].col_offset,
            nesting_level=depth,
            summary="else block",
            description=f"Else branch, lines {start} to {end}",
            parent_id=parent_id
        )

    def _create_except_node(self, handler: ast.ExceptHandler, depth: int, parent_id: Optional[str]) -> CodeNode:
        name = ast.unparse(handler.type) if handler.type else "Exception"
        as_name = f" as {handler.name}" if handler.name else ""
        summary = f"except {name}{as_name}"
        start = handler.lineno
        end = getattr(handler, "end_lineno", handler.lineno)
        return CodeNode(
            id=self._next_id(),
            node_type="ExceptHandler",
            name=summary,
            start_line=start,
            end_line=end,
            col_offset=handler.col_offset,
            nesting_level=depth,
            summary=summary,
            description=f"Exception handler catching {name}{as_name}, lines {start} to {end}",
            parent_id=parent_id
        )

    def _generate_syntax_advice(self, se: SyntaxError, lines: List[str]) -> str:
        line_num = se.lineno or 1
        col_num = se.offset or 1
        msg = str(se.msg)
        offending_line = lines[line_num - 1] if 0 < line_num <= len(lines) else ""

        if "expected ':'" in msg.lower():
            return f"Syntax error at line {line_num}: You are missing a colon ':' at the end of statement '{offending_line.strip()}'. Press Enter and type a colon."
        if "unindent does not match" in msg.lower() or "indentationerror" in type(se).__name__.lower():
            return f"Indentation error at line {line_num}: The indentation does not align with the surrounding block. Check spaces or tabs on line {line_num}."
        if "was never closed" in msg.lower() or "unexpected EOF" in msg:
            return f"Unclosed bracket or parenthesis detected around line {line_num}. Make sure every opening parenthesis, bracket, or quotation mark has a matching closing symbol."
        if "invalid syntax" in msg.lower():
            return f"Syntax error at line {line_num}, column {col_num}. The Python parser stopped at '{offending_line.strip()}'. Check for typos, misspelled keywords, or missing punctuation."
        
        return f"Syntax error: {msg} at line {line_num}, column {col_num}."

    def find_node_at_line(self, result: CodeAnalysisResult, line: int) -> Optional[CodeNode]:
        best: Optional[CodeNode] = None
        for node in result.flattened_nodes:
            if node.start_line <= line <= node.end_line:
                if best is None or (node.end_line - node.start_line) <= (best.end_line - best.start_line):
                    best = node
        return best
