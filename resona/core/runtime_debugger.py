"""
RESONA Runtime Debugger and Execution Tracer (High-Performance Engine)
Instruments Python code execution using sys.settrace with O(1) call depth tracking,
variable mutation diffing, time-travel history replay, and loop protection.
"""

from __future__ import annotations
import sys
import io
import time
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any, Optional, Set


@dataclass
class VariableChange:
    """Represents a mutation to a local variable during an execution step."""
    name: str
    old_value: Optional[str]
    new_value: str
    is_new: bool = False


@dataclass
class ExecutionEvent:
    """Represents a single atomic execution step recorded by the tracer."""
    step_index: int
    event_type: str  # 'line', 'call', 'return', 'exception'
    line_number: int
    function_name: str
    call_depth: int
    locals_snapshot: Dict[str, str]
    variable_changes: List[VariableChange]
    stdout_chunk: str = ""
    code_text: str = ""
    exception_info: Optional[Dict[str, str]] = None
    timestamp: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "step_index": self.step_index,
            "event_type": self.event_type,
            "line_number": self.line_number,
            "function_name": self.function_name,
            "call_depth": self.call_depth,
            "locals_snapshot": self.locals_snapshot,
            "variable_changes": [asdict(vc) for vc in self.variable_changes],
            "stdout_chunk": self.stdout_chunk,
            "code_text": self.code_text,
            "exception_info": self.exception_info,
            "timestamp": self.timestamp
        }


@dataclass
class RuntimeExecutionResult:
    """Complete recorded trace and outcome of a program execution."""
    success: bool
    total_steps: int
    events: List[ExecutionEvent]
    full_stdout: str
    full_stderr: str
    error_message: Optional[str] = None
    error_type: Optional[str] = None
    error_line: Optional[int] = None
    timed_out: bool = False
    loop_limit_exceeded: bool = False
    execution_time_seconds: float = 0.0
    breakpoints_hit: List[int] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "total_steps": self.total_steps,
            "events": [e.to_dict() for e in self.events],
            "full_stdout": self.full_stdout,
            "full_stderr": self.full_stderr,
            "error_message": self.error_message,
            "error_type": self.error_type,
            "error_line": self.error_line,
            "timed_out": self.timed_out,
            "loop_limit_exceeded": self.loop_limit_exceeded,
            "execution_time_seconds": self.execution_time_seconds,
            "breakpoints_hit": self.breakpoints_hit
        }


class RuntimeDebugger:
    """
    Safely executes Python source code under trace monitoring.
    Optimized for high-speed sub-millisecond execution and minimal allocation.
    """

    def __init__(self, max_steps: int = 1500, timeout_seconds: float = 5.0):
        self.max_steps = max_steps
        self.timeout_seconds = timeout_seconds

    def execute_and_trace(self, source_code: str, breakpoints: Optional[Set[int]] = None) -> RuntimeExecutionResult:
        if breakpoints is None:
            breakpoints = set()

        events: List[ExecutionEvent] = []
        breakpoints_hit: List[int] = []
        lines = source_code.splitlines()

        # Capture stdout and stderr
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        captured_stdout = io.StringIO()
        captured_stderr = io.StringIO()
        sys.stdout = captured_stdout
        sys.stderr = captured_stderr

        start_time = time.time()
        step_counter = 0
        timed_out = False
        loop_limit_exceeded = False
        last_locals: Dict[str, str] = {}
        last_stdout_pos = 0
        curr_depth = 0

        target_filename = "<resona_session>"

        def tracer(frame, event, arg):
            nonlocal step_counter, timed_out, loop_limit_exceeded, last_locals, last_stdout_pos, curr_depth

            if loop_limit_exceeded or timed_out:
                return None

            if frame.f_code.co_filename != target_filename:
                return tracer

            if time.time() - start_time > self.timeout_seconds:
                timed_out = True
                sys.settrace(None)
                raise TimeoutError("Execution timed out (possible infinite loop)")

            if step_counter >= self.max_steps:
                loop_limit_exceeded = True
                sys.settrace(None)
                raise RuntimeError(f"Execution step limit ({self.max_steps}) exceeded")

            # O(1) depth maintenance
            if event == "call":
                curr_depth += 1
            elif event == "return":
                curr_depth = max(0, curr_depth - 1)

            line_no = frame.f_lineno
            func_name = frame.f_code.co_name
            if func_name == "<module>":
                func_name = "main"

            # Fast serialization of local variables
            current_locals: Dict[str, str] = {}
            var_changes: List[VariableChange] = []

            for k, v in frame.f_locals.items():
                if k.startswith("__"):
                    continue
                try:
                    repr_v = repr(v)
                    if len(repr_v) > 50:
                        repr_v = repr_v[:47] + "..."
                    current_locals[k] = repr_v

                    if k not in last_locals:
                        var_changes.append(VariableChange(name=k, old_value=None, new_value=repr_v, is_new=True))
                    elif last_locals[k] != repr_v:
                        var_changes.append(VariableChange(name=k, old_value=last_locals[k], new_value=repr_v, is_new=False))
                except Exception:
                    current_locals[k] = "<unprintable>"

            last_locals = dict(current_locals)

            # Retrieve stdout delta
            curr_stdout_str = captured_stdout.getvalue()
            new_stdout_chunk = curr_stdout_str[last_stdout_pos:]
            last_stdout_pos = len(curr_stdout_str)

            code_text = lines[line_no - 1].strip() if 0 < line_no <= len(lines) else ""

            exc_info = None
            if event == "exception":
                exc_type, exc_val, _ = arg
                exc_info = {
                    "type": exc_type.__name__ if exc_type else "Exception",
                    "message": str(exc_val) if exc_val else ""
                }

            events.append(ExecutionEvent(
                step_index=step_counter,
                event_type=event,
                line_number=line_no,
                function_name=func_name,
                call_depth=curr_depth,
                locals_snapshot=current_locals,
                variable_changes=var_changes,
                stdout_chunk=new_stdout_chunk,
                code_text=code_text,
                exception_info=exc_info,
                timestamp=time.time() - start_time
            ))

            if line_no in breakpoints and line_no not in breakpoints_hit:
                breakpoints_hit.append(line_no)

            step_counter += 1
            return tracer

        success = True
        error_msg = None
        error_type = None
        error_line = None

        try:
            compiled_code = compile(source_code, target_filename, "exec")
            sys.settrace(tracer)
            exec_namespace = {
                "__name__": "__main__",
                "__doc__": None,
                "__package__": None,
            }
            exec(compiled_code, exec_namespace)
        except TimeoutError as te:
            success = False
            timed_out = True
            error_msg = str(te)
            error_type = "TimeoutError"
            error_line = events[-1].line_number if events else None
        except RuntimeError as re:
            success = False
            error_msg = str(re)
            error_type = "LoopLimitExceeded" if loop_limit_exceeded else type(re).__name__
            error_line = events[-1].line_number if events else None
        except Exception as e:
            success = False
            error_msg = str(e)
            error_type = type(e).__name__
            tb = sys.exc_info()[2]
            while tb:
                if tb.tb_frame.f_code.co_filename == target_filename:
                    error_line = tb.tb_lineno
                tb = tb.tb_next
            if error_line is None and events:
                error_line = events[-1].line_number
        finally:
            sys.settrace(None)
            sys.stdout = old_stdout
            sys.stderr = old_stderr

        elapsed = time.time() - start_time

        return RuntimeExecutionResult(
            success=success,
            total_steps=len(events),
            events=events,
            full_stdout=captured_stdout.getvalue(),
            full_stderr=captured_stderr.getvalue(),
            error_message=error_msg,
            error_type=error_type,
            error_line=error_line,
            timed_out=timed_out,
            loop_limit_exceeded=loop_limit_exceeded,
            execution_time_seconds=round(elapsed, 4),
            breakpoints_hit=breakpoints_hit
        )
