"""
Unit tests for RESONA Runtime Debugger & Tracer
"""

from resona.core.runtime_debugger import RuntimeDebugger


def test_successful_trace():
    debugger = RuntimeDebugger()
    code = """
total = 0
for i in range(4):
    total += i
print("Done", total)
"""
    result = debugger.execute_and_trace(code)
    assert result.success is True
    assert result.total_steps > 0
    assert "Done 6" in result.full_stdout.strip()
    assert result.error_message is None

    # Check that variable updates were recorded
    has_total_update = any(
        any(vc.name == "total" for vc in ev.variable_changes)
        for ev in result.events
    )
    assert has_total_update is True


def test_exception_capture():
    debugger = RuntimeDebugger()
    code = """
nums = [1, 2]
print(nums[10])
"""
    result = debugger.execute_and_trace(code)
    assert result.success is False
    assert result.error_type == "IndexError"
    assert result.error_line == 3
    assert len(result.events) > 0


def test_infinite_loop_timeout_protection():
    debugger = RuntimeDebugger(max_steps=50, timeout_seconds=1.0)
    code = """
x = 0
while True:
    x += 1
"""
    result = debugger.execute_and_trace(code)
    assert result.success is False
    assert result.timed_out is True or result.loop_limit_exceeded is True
