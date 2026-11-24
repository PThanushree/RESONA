"""
Unit tests for Context Engine & AI Narrator
"""

from resona.core.ast_analyzer import ASTAnalyzer
from resona.core.runtime_debugger import RuntimeDebugger
from resona.core.ai_narrator import AINarrator


def test_explain_binary_search_algorithm():
    code = """
def binary_search(arr, target):
    low = 0
    high = len(arr) - 1
    while low <= high:
        mid = (low + high) // 2
        if arr[mid] == target:
            return mid
        elif arr[mid] < target:
            low = mid + 1
        else:
            high = mid - 1
    return -1
"""
    analyzer = ASTAnalyzer()
    analysis = analyzer.analyze(code)
    narrator = AINarrator()

    overview = narrator.explain_code_structure(analysis, code)
    assert "binary_search" in overview["narrative"].lower()
    assert "binary search" in overview["detected_pattern"].lower()


def test_diagnose_off_by_one_index_error():
    code = """
items = [10, 20]
for i in range(3):
    val = items[i]
"""
    debugger = RuntimeDebugger()
    trace = debugger.execute_and_trace(code)
    narrator = AINarrator()

    diag = narrator.diagnose_error(trace, code)
    assert diag["error_type"] == "IndexError"
    assert "boundary" in diag["narrative"].lower() or "bounds" in diag["narrative"].lower() or "outside" in diag["narrative"].lower()
    assert "0-indexed" in diag["fix_recommendation"].lower()
