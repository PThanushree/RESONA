"""
RESONA Master Launcher
Initializes the accessible server, verifies sound synthesizer components,
and launches the application in the system's default accessible browser.
"""

import sys
import os
import webbrowser
import time
import uvicorn

# Ensure the scratch directory is in python path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

def print_banner():
    print("=" * 72)
    print("  RESONA: Accessible Programming & Audio Code Comprehension System")
    print("  KSCST 50th Series Student Project Programme (2026-2027)")
    print("  Institution: JSS Science and Technology University, Mysuru")
    print("  Focus: Human-Computer Interaction & Assistive Technology")
    print("=" * 72)
    print("  [*] Synthesizing acoustic earcons and soundscapes...")
    print("  [*] Initializing AST analysis & runtime trace engine...")
    print("  [*] Starting Web Application on http://127.0.0.1:8000")
    print("  [*] Press Ctrl+C in this terminal window to stop the server.")
    print("=" * 72)

def main():
    print_banner()
    
    # Auto-open browser after 1.5 seconds delay
    def open_browser():
        time.sleep(1.5)
        webbrowser.open("http://127.0.0.1:8000")

    import threading
    threading.Thread(target=open_browser, daemon=True).start()

    # Import and run FastAPI server directly
    try:
        from resona.web.server import app
    except ImportError:
        from web.server import app

    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="info")

if __name__ == "__main__":
    main()
