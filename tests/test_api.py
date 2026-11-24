"""
Integration tests for FastAPI endpoints (Direct invocation)
"""

import json
from resona.web.server import (
    health_check,
    serve_index,
    analyze_code,
    run_code,
    narrate_code,
    process_pipeline,
    get_example,
    get_earcon_audio,
    CodeRequest
)


def test_health_endpoint():
    res = health_check()
    assert res["status"] == "ok"
    assert res["app"] == "RESONA"


def test_serve_html():
    res = serve_index()
    content = res.body.decode("utf-8") if hasattr(res, "body") else str(res)
    assert "RESONA" in content
    assert "main-workspace" in content


def test_api_analyze():
    req = CodeRequest(code="def sample(x):\n    return x * 2\n")
    res = analyze_code(req)
    data = json.loads(res.body.decode())
    assert data["is_valid"] is True
    assert data["total_functions"] == 1


def test_api_run():
    req = CodeRequest(code="val = 42\nprint(val)\n")
    res = run_code(req)
    data = json.loads(res.body.decode())
    assert data["success"] is True
    assert "42" in data["full_stdout"]


def test_api_narrate():
    req = CodeRequest(code="def greet(name):\n    print('Hello', name)\ngreet('World')\n")
    res = narrate_code(req)
    data = json.loads(res.body.decode())
    assert "structure" in data
    assert "runtime" in data


def test_api_example():
    res = get_example("01_binary_search.py")
    data = json.loads(res.body.decode())
    assert "binary_search" in data["code"]


def test_api_audio():
    res = get_earcon_audio("function_entry")
    assert res.media_type == "audio/wav"
    assert len(res.body) > 44


def test_api_pipeline():
    req = CodeRequest(code="def compute(n):\n    s = 0\n    for i in range(n):\n        s += i\n    return s\nprint(compute(5))\n")
    res = process_pipeline(req)
    data = json.loads(res.body.decode())
    assert data["analysis"]["is_valid"] is True
    assert data["trace"]["success"] is True
    assert "10" in data["trace"]["full_stdout"]
    assert len(data["soundscape"]) > 0
    assert "structure" in data["narration"]
    assert "runtime" in data["narration"]

