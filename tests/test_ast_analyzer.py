"""
Unit tests for RESONA AST Analyzer
"""

from resona.core.ast_analyzer import ASTAnalyzer


def test_analyze_simple_function():
    analyzer = ASTAnalyzer()
    code = """
def add(a, b):
    return a + b
"""
    result = analyzer.analyze(code)
    assert result.is_valid is True
    assert result.total_functions == 1
    assert result.total_classes == 0
    assert result.total_loops == 0

    func_node = next(n for n in result.flattened_nodes if n.node_type == "FunctionDef")
    assert func_node.name == "add"
    assert func_node.parameters == ["a", "b"]
    assert func_node.nesting_level == 1


def test_analyze_nested_constructs():
    analyzer = ASTAnalyzer()
    code = """
class DataProcessor:
    def process(self, items):
        for item in items:
            if item > 0:
                print(item)
"""
    result = analyzer.analyze(code)
    assert result.is_valid is True
    assert result.total_classes == 1
    assert result.total_functions == 1
    assert result.total_loops == 1
    assert result.total_branches == 1
    assert result.max_nesting_depth == 5


def test_syntax_error_handling():
    analyzer = ASTAnalyzer()
    code = """
def faulty_syntax(
    print("missing closing paren"
"""
    result = analyzer.analyze(code)
    assert result.is_valid is False
    assert result.syntax_error is not None
    assert result.syntax_error.line > 0
    assert "syntax" in result.syntax_error.spoken_advice.lower() or "unclosed" in result.syntax_error.spoken_advice.lower()


def test_find_node_at_line():
    analyzer = ASTAnalyzer()
    code = """def first():
    x = 10
    return x

def second():
    y = 20
    return y
"""
    result = analyzer.analyze(code)
    node_at_line_2 = analyzer.find_node_at_line(result, 2)
    assert node_at_line_2 is not None
    assert "x" in node_at_line_2.name or node_at_line_2.node_type == "Assign"
