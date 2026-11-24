"""
RESONA Test Suite Runner (Pure Python - No external test dependencies needed)
Discovers and executes all test functions across the test suite.
"""

import sys
import os
import inspect
import traceback
from rich.console import Console
from rich.table import Table

console = Console()

# Ensure scratch path is in sys.path
TEST_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(TEST_DIR)
SCRATCH_DIR = os.path.dirname(PROJECT_DIR)

for p in (SCRATCH_DIR, PROJECT_DIR):
    if p not in sys.path:
        sys.path.insert(0, p)


def run_all_tests():
    console.print("[bold cyan]====================================================================[/bold cyan]")
    console.print("[bold yellow]       RESONA TEST SUITE - KSCST QUALITY VERIFICATION[/bold yellow]")
    console.print("[bold cyan]====================================================================[/bold cyan]")

    test_files = [
        "test_ast_analyzer.py",
        "test_runtime_debugger.py",
        "test_sonification.py",
        "test_ai_narrator.py",
        "test_api.py"
    ]

    total_passed = 0
    total_failed = 0
    failures = []

    table = Table(title="Test Execution Summary")
    table.add_column("Module / File", style="cyan")
    table.add_column("Test Function", style="white")
    table.add_column("Status", justify="center")

    for tf in test_files:
        filepath = os.path.join(TEST_DIR, tf)
        if not os.path.exists(filepath):
            continue

        mod_name = tf.replace(".py", "")
        # Import module dynamically
        import importlib.util
        spec = importlib.util.spec_from_file_location(f"resona.tests.{mod_name}", filepath)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)

        # Find all test_ functions
        for name, func in inspect.getmembers(mod, inspect.isfunction):
            if name.startswith("test_"):
                print(f"Running {tf} -> {name}...", flush=True)
                try:
                    func()
                    total_passed += 1
                    table.add_row(tf, name, "[bold green]PASS[/bold green]")
                except Exception as ex:
                    total_failed += 1
                    failures.append((tf, name, traceback.format_exc()))
                    table.add_row(tf, name, "[bold red]FAIL[/bold red]")

    console.print(table)

    if failures:
        console.print("\n[bold red]FAILURE DETAILS:[/bold red]")
        for tf, name, err in failures:
            console.print(f"[bold red]In {tf} -> {name}:[/bold red]")
            console.print(err)
            console.print("-" * 60)

    console.print(f"\n[bold]Total Tests:[/bold] {total_passed + total_failed} | "
                  f"[bold green]Passed:[/bold green] {total_passed} | "
                  f"[bold red]Failed:[/bold red] {total_failed}")

    if total_failed > 0:
        sys.exit(1)
    else:
        console.print("[bold green]ALL TESTS PASSED WITH 100% SUCCESS![/bold green]")


if __name__ == "__main__":
    run_all_tests()
