"""
RESONA Sonification Engine
Maps AST syntactic hierarchy and runtime execution events to auditory dimensions
including frequency, stereo panning, harmonic timbre, and rhythmic earcons.
"""

from __future__ import annotations
from typing import Dict, Any, List, Optional
from resona.core.ast_analyzer import CodeNode, CodeAnalysisResult
from resona.core.runtime_debugger import ExecutionEvent, RuntimeExecutionResult


class SonificationEngine:
    """
    Transforms code structure and runtime dynamics into auditory parameters.
    Based on research in non-visual program sonification (Potluri et al., Metatla et al.).
    """

    # Scale mapping nesting depth to musical frequencies (Hz)
    DEPTH_FREQUENCIES = [
        261.63,  # Depth 0: C4 (Root)
        293.66,  # Depth 1: D4
        329.63,  # Depth 2: E4
        392.00,  # Depth 3: G4
        440.00,  # Depth 4: A4
        523.25,  # Depth 5: C5
        587.33,  # Depth 6: D5
        659.25   # Depth 7+: E5
    ]

    def __init__(self):
        pass

    def get_frequency_for_depth(self, depth: int) -> float:
        """Get the pitch corresponding to code indentation / nesting depth."""
        idx = max(0, min(depth, len(self.DEPTH_FREQUENCIES) - 1))
        return self.DEPTH_FREQUENCIES[idx]

    def map_ast_node(self, node: CodeNode, total_lines: int = 1) -> Dict[str, Any]:
        """Compute auditory properties for an AST structural element."""
        freq = self.get_frequency_for_depth(node.nesting_level)
        pan = -1.0 + (2.0 * min(node.start_line / max(total_lines, 1), 1.0))

        earcon_id = "indent_level_0"
        if node.node_type in ("FunctionDef", "AsyncFunctionDef"):
            earcon_id = "function_entry"
        elif node.node_type == "ClassDef":
            earcon_id = "class_entry"
        elif node.node_type in ("For", "While"):
            earcon_id = "loop_iteration"
        elif node.node_type in ("If", "Elif"):
            earcon_id = "branch_true"
        elif node.node_type == "Else":
            earcon_id = "branch_false"
        elif node.node_type == "Return":
            earcon_id = "function_return"
        else:
            earcon_id = f"indent_level_{min(node.nesting_level, 7)}"

        return {
            "node_id": node.id,
            "earcon_id": earcon_id,
            "frequency_hz": freq,
            "nesting_level": node.nesting_level,
            "stereo_pan": round(pan, 2),
            "line": node.start_line,
            "label": node.summary
        }

    def map_runtime_event(self, event: ExecutionEvent, prev_event: Optional[ExecutionEvent] = None, total_lines: int = 1) -> Dict[str, Any]:
        """Determine the acoustic earcon and parameter modulation for a runtime trace step."""
        freq = self.get_frequency_for_depth(event.call_depth)
        pan = -1.0 + (2.0 * min(event.line_number / max(total_lines, 1), 1.0))
        earcon_id = "step_tick"

        spoken_hint = f"Line {event.line_number}: {event.code_text}"

        if event.event_type == "exception":
            earcon_id = "runtime_error"
            exc_type = event.exception_info.get("type", "Error") if event.exception_info else "Error"
            exc_msg = event.exception_info.get("message", "") if event.exception_info else ""
            spoken_hint = f"Exception {exc_type} at line {event.line_number}: {exc_msg}"

        elif event.event_type == "call":
            earcon_id = "function_entry"
            spoken_hint = f"Entering function {event.function_name} at line {event.line_number}"

        elif event.event_type == "return":
            earcon_id = "function_return"
            spoken_hint = f"Returning from function {event.function_name}"

        elif event.variable_changes:
            earcon_id = "variable_change"
            # Highlight variable delta in spoken hint
            deltas = [f"{vc.name} became {vc.new_value}" for vc in event.variable_changes]
            spoken_hint = f"Line {event.line_number}: {', '.join(deltas)}"

        elif "for " in event.code_text or "while " in event.code_text:
            earcon_id = "loop_iteration"

        elif "if " in event.code_text or "elif " in event.code_text:
            earcon_id = "branch_true"

        return {
            "step_index": event.step_index,
            "line_number": event.line_number,
            "event_type": event.event_type,
            "earcon_id": earcon_id,
            "frequency_hz": freq,
            "stereo_pan": round(pan, 2),
            "spoken_hint": spoken_hint,
            "has_var_change": bool(event.variable_changes),
            "has_stdout": bool(event.stdout_chunk)
        }

    def generate_trace_soundscape(self, result: RuntimeExecutionResult, total_lines: int = 1) -> List[Dict[str, Any]]:
        """Generate a complete chronological audio sequence for the entire execution."""
        soundscape = []
        prev: Optional[ExecutionEvent] = None
        for ev in result.events:
            mapping = self.map_runtime_event(ev, prev, total_lines)
            soundscape.append(mapping)
            prev = ev

        if result.success:
            soundscape.append({
                "step_index": len(result.events),
                "line_number": 0,
                "event_type": "finish",
                "earcon_id": "execution_success",
                "frequency_hz": 523.25,
                "stereo_pan": 0.0,
                "spoken_hint": "Execution finished successfully.",
                "has_var_change": False,
                "has_stdout": False
            })
        return soundscape
