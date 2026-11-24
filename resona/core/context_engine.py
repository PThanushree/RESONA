"""
RESONA Context Engine Module (Phase 4 of Methodology)
Maintains dynamic contextual representation combining AST structure,
user navigation focus, execution history, variable scopes, and interaction state.
Feeds contextual knowledge to the AI Code Understanding engine and audio pipeline.
"""

from __future__ import annotations
import time
from dataclasses import dataclass, field, asdict
from typing import Dict, Any, List, Optional
from resona.core.ast_analyzer import CodeAnalysisResult, CodeNode, ScopeInfo
from resona.core.runtime_debugger import RuntimeExecutionResult, ExecutionEvent


@dataclass
class CursorContext:
    """Snapshot of the developer's current focus in the program."""
    line_number: int
    column_offset: int
    enclosing_node_name: str
    enclosing_node_type: str
    nesting_depth: int
    active_scope_name: str
    variables_in_scope: List[str]
    is_executed: bool
    execution_hit_count: int
    last_runtime_value: Optional[str] = None
    spoken_summary: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class ContextEngine:
    """
    Central state engine for non-visual programming context.
    Aggregates static syntactic structures, dynamic trace events, and user navigation history.
    """

    def __init__(self):
        self.current_code: str = ""
        self.current_analysis: Optional[CodeAnalysisResult] = None
        self.current_trace: Optional[RuntimeExecutionResult] = None
        self.navigation_history: List[int] = []  # History of visited lines
        self.active_line: int = 1
        self.active_step_index: int = 0
        self.session_start_time: float = time.time()

    def update_code(self, source_code: str, analysis: CodeAnalysisResult):
        """Update static code structure context."""
        self.current_code = source_code
        self.current_analysis = analysis

    def update_trace(self, trace_result: RuntimeExecutionResult):
        """Update dynamic runtime execution trace context."""
        self.current_trace = trace_result
        self.active_step_index = 0

    def record_navigation(self, line: int):
        """Track user navigation path through the codebase."""
        self.active_line = line
        self.navigation_history.append(line)
        if len(self.navigation_history) > 100:
            self.navigation_history.pop(0)

    def get_cursor_context(self, line_number: int) -> CursorContext:
        """
        Derive rich contextual information for any given line number.
        Answers: 'Where am I, what scope is active, what variables exist, and did this run?'
        """
        self.active_line = line_number
        self.record_navigation(line_number)

        node_name = "Module"
        node_type = "Module"
        depth = 0
        scope_name = "global"
        vars_in_scope: List[str] = []

        if self.current_analysis and self.current_analysis.is_valid:
            # Find innermost enclosing node
            best_node = None
            for n in self.current_analysis.flattened_nodes:
                if n.start_line <= line_number <= n.end_line:
                    if best_node is None or (n.end_line - n.start_line) <= (best_node.end_line - best_node.start_line):
                        best_node = n
            if best_node:
                node_name = best_node.name
                node_type = best_node.node_type
                depth = best_node.nesting_level

            # Find matching variable scope
            for sc in self.current_analysis.variable_scopes:
                if sc.start_line <= line_number <= sc.end_line:
                    scope_name = f"{sc.scope_type}: {sc.name}"
                    vars_in_scope = list(set(sc.variables_defined + sc.parameters))

        # Runtime hit counting and execution status
        hit_count = 0
        last_val = None
        if self.current_trace and self.current_trace.events:
            matching_events = [e for e in self.current_trace.events if e.line_number == line_number]
            hit_count = len(matching_events)
            if matching_events:
                last_ev = matching_events[-1]
                if last_ev.variable_changes:
                    last_val = ", ".join(f"{vc.name}={vc.new_value}" for vc in last_ev.variable_changes)
                elif last_ev.locals_snapshot:
                    sample_vars = list(last_ev.locals_snapshot.items())[:3]
                    last_val = ", ".join(f"{k}={v}" for k, v in sample_vars)

        is_executed = hit_count > 0
        exec_desc = f"executed {hit_count} time{'s' if hit_count != 1 else ''}" if is_executed else "not reached in trace"

        spoken = f"Line {line_number}, inside {node_type} {node_name}, nesting depth {depth}. Scope: {scope_name}. {exec_desc}."

        return CursorContext(
            line_number=line_number,
            column_offset=0,
            enclosing_node_name=node_name,
            enclosing_node_type=node_type,
            nesting_depth=depth,
            active_scope_name=scope_name,
            variables_in_scope=vars_in_scope,
            is_executed=is_executed,
            execution_hit_count=hit_count,
            last_runtime_value=last_val,
            spoken_summary=spoken
        )

    def build_llm_prompt_context(self, user_question: Optional[str] = None) -> str:
        """
        Synthesize AST structure, cursor context, variable scopes, and execution trace
        into a structured prompt context for AI code understanding (Phase 5).
        """
        cursor = self.get_cursor_context(self.active_line)
        lines = self.current_code.splitlines()
        code_with_lines = "\n".join(f"{i+1:3d}: {line}" for i, line in enumerate(lines))

        prompt_parts = [
            "### SOURCE CODE:",
            code_with_lines,
            "",
            "### AST CODE STRUCTURE & SCOPE CONTEXT:",
            f"- Total Lines: {len(lines)}",
            f"- Active Cursor Line: {cursor.line_number}",
            f"- Active Enclosing Node: {cursor.enclosing_node_type} '{cursor.enclosing_node_name}' (Depth {cursor.nesting_depth})",
            f"- Active Lexical Scope: {cursor.active_scope_name}",
            f"- Variables in Active Scope: {', '.join(cursor.variables_in_scope) if cursor.variables_in_scope else 'None'}"
        ]

        if self.current_analysis and self.current_analysis.variable_scopes:
            prompt_parts.append("\n### VARIABLE SCOPES:")
            for sc in self.current_analysis.variable_scopes:
                shadow_str = f" [Shadows: {', '.join(sc.shadowed_variables)}]" if sc.shadowed_variables else ""
                prompt_parts.append(f"- Scope '{sc.name}' ({sc.scope_type}, lines {sc.start_line}-{sc.end_line}): defined={sc.variables_defined}, params={sc.parameters}{shadow_str}")

        if self.current_trace:
            prompt_parts.append("\n### RUNTIME EXECUTION CONTEXT:")
            prompt_parts.append(f"- Status: {'SUCCESS' if self.current_trace.success else 'FAILED'}")
            prompt_parts.append(f"- Total Steps: {self.current_trace.total_steps}")
            if not self.current_trace.success:
                prompt_parts.append(f"- Error: {self.current_trace.error_type} at line {self.current_trace.error_line}: {self.current_trace.error_message}")
            if self.current_trace.full_stdout.strip():
                prompt_parts.append(f"- Program Output: '{self.current_trace.full_stdout.strip()}'")

        if user_question:
            prompt_parts.append(f"\n### USER ACCESSIBILITY QUESTION:\n{user_question}")
            prompt_parts.append("\nProvide a clear, direct, accessible explanation for a visually impaired programmer. Focus on code logic, spatial flow, and fixes.")

        return "\n".join(prompt_parts)
