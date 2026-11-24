"""
RESONA Accessible Command Line Interface
Terminal-based assistive tool with speech synthesis and acoustic sonification.
Designed for screen-reader terminal workflows (NVDA/JAWS/Orca).
"""

from __future__ import annotations
import sys
import os
import argparse
import time
from typing import Optional

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.tree import Tree

from resona.core.ast_analyzer import ASTAnalyzer, CodeAnalysisResult
from resona.core.runtime_debugger import RuntimeDebugger, RuntimeExecutionResult
from resona.core.sonification_engine import SonificationEngine
from resona.core.ai_narrator import AINarrator
from resona.core.audio_synthesizer import AudioSynthesizer

console = Console()


def speak_cli(text: str):
    """Attempt cross-platform or Windows text-to-speech for terminal accessibility."""
    try:
        import winsound
        # Subtle notification beep
        winsound.Beep(880, 50)
    except Exception:
        pass


def play_terminal_earcon(earcon_name: str):
    """Play acoustic feedback directly in terminal on Windows."""
    try:
        import winsound
        if earcon_name == "function_entry":
            winsound.Beep(523, 70)
            winsound.Beep(659, 70)
            winsound.Beep(784, 100)
        elif earcon_name == "loop_iteration":
            winsound.Beep(440, 40)
            winsound.Beep(440, 40)
        elif earcon_name == "branch_true":
            winsound.Beep(988, 80)
        elif earcon_name == "branch_false":
            winsound.Beep(349, 80)
        elif earcon_name == "runtime_error":
            winsound.Beep(262, 120)
            winsound.Beep(370, 200)
        elif earcon_name == "execution_success":
            winsound.Beep(523, 80)
            winsound.Beep(659, 80)
            winsound.Beep(1046, 160)
        else:
            winsound.Beep(600, 50)
    except Exception:
        pass


def display_ast_tree(analysis: CodeAnalysisResult):
    """Render an accessible high-contrast tree view in terminal."""
    if not analysis.is_valid:
        err = analysis.syntax_error
        console.print(Panel(
            f"[bold red]Syntax Error at Line {err.line if err else '?'}[/bold red]\n"
            f"[yellow]{err.spoken_advice if err else 'Invalid syntax'}[/yellow]",
            title="[bold red]Parsing Failed[/bold red]"
        ))
        return

    tree = Tree(f"[bold cyan]Module Root[/bold cyan] ({analysis.total_lines} lines)")
    nodes_by_id = {n.id: n for n in analysis.flattened_nodes}

    def add_children(parent_node, parent_tree):
        for child in parent_node.children:
            color = "green" if "Function" in child.node_type else "yellow" if child.node_type in ("For", "While") else "magenta" if "Class" in child.node_type else "cyan"
            branch = parent_tree.add(f"[{color}][bold]{child.node_type}:[/bold] {child.name}[/{color}] (Line {child.start_line}, Depth {child.nesting_level})")
            add_children(child, branch)

    if analysis.root_node:
        add_children(analysis.root_node, tree)

    console.print(tree)


def run_cli_interactive(filepath: str, step_mode: bool = False):
    """Run full analysis, execution tracing, and AI narration in terminal."""
    if not os.path.exists(filepath):
        console.print(f"[bold red]File not found:[/bold red] {filepath}")
        sys.exit(1)

    with open(filepath, "r", encoding="utf-8") as f:
        source_code = f.read()

    console.print(Panel(
        f"[bold cyan]RESONA Accessible Engine[/bold cyan]\n"
        f"KSCST 50th Series | JSS Science & Technology University, Mysuru\n"
        f"Analyzing: [bold green]{os.path.basename(filepath)}[/bold green]",
        title="[bold yellow]Non-Visual Program Comprehension[/bold yellow]"
    ))

    # 1. AST Analysis
    analyzer = ASTAnalyzer()
    analysis = analyzer.analyze(source_code)

    console.print("\n[bold yellow]--- [1] AST Hierarchy & Structural Landmarks ---[/bold yellow]")
    display_ast_tree(analysis)

    # 2. AI Code Explanation
    narrator = AINarrator()
    overview = narrator.explain_code_structure(analysis, source_code)
    console.print("\n[bold yellow]--- [2] AI Contextual Overview ---[/bold yellow]")
    console.print(Panel(overview["narrative"], title=f"[bold green]{overview['headline']}[/bold green]"))

    # 3. Runtime Debugging & Tracing
    if analysis.is_valid:
        console.print("\n[bold yellow]--- [3] Runtime Execution Trace ---[/bold yellow]")
        debugger = RuntimeDebugger()
        trace = debugger.execute_and_trace(source_code)

        if step_mode:
            console.print(f"[cyan]Stepping through {trace.total_steps} execution events. Press ENTER to advance...[/cyan]")
            for ev in trace.events:
                play_terminal_earcon(ev.event_type if ev.event_type in ("exception", "call", "return") else "step_tick")
                console.print(f"[bold]Step {ev.step_index + 1}[/bold] | Line {ev.line_number} | {ev.event_type.upper()} | [green]{ev.code_text}[/green]")
                if ev.variable_changes:
                    changes_str = ", ".join(f"{vc.name} = {vc.new_value}" for vc in ev.variable_changes)
                    console.print(f"  [yellow]Mutations:[/yellow] {changes_str}")
                input("  [Press Enter to continue...]")

        if trace.success:
            play_terminal_earcon("execution_success")
            runtime_info = narrator.explain_runtime_trace(trace, source_code)
            console.print(Panel(
                f"[bold green]{runtime_info['headline']}[/bold green]\n"
                f"{runtime_info['narrative']}\n\n"
                f"[bold cyan]Stdout Output:[/bold cyan]\n{trace.full_stdout.strip() if trace.full_stdout else '(None)'}",
                title="[bold green]Execution Successful[/bold green]"
            ))
        else:
            play_terminal_earcon("runtime_error")
            err_diag = narrator.diagnose_error(trace, source_code)
            console.print(Panel(
                f"[bold red]{err_diag['headline']}[/bold red]\n"
                f"{err_diag['narrative']}\n\n"
                f"[bold yellow]Recommended Fix:[/bold yellow]\n{err_diag['fix_recommendation']}",
                title="[bold red]Runtime Error Diagnosed[/bold red]"
            ))


def main():
    parser = argparse.ArgumentParser(description="RESONA Accessible Code Comprehension System (KSCST)")
    parser.add_argument("file", nargs="?", help="Path to Python source file to analyze and run")
    parser.add_argument("--step", action="store_true", help="Enable interactive step-by-step debugger playback with audio")
    args = parser.parse_args()

    if args.file:
        run_cli_interactive(args.file, step_mode=args.step)
    else:
        # Default to binary search example
        default_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), "examples", "01_binary_search.py")
        run_cli_interactive(default_file, step_mode=False)


if __name__ == "__main__":
    main()
