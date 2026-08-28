"""
Ship Crew Optimizer - Desktop Application Launcher

Integrates Flask API with PyWebView for a native desktop application.
Starts Flask server on a background thread and opens a PyWebView window.

Usage:
    python app.py
"""

import threading
import sys
import os

import flask
from flask import render_template
import webview

# Import Flask API app
from api import app as flask_app, ROSTER_FILE, SHIP_CONFIG_FILE

# Configuration
HOST = "127.0.0.1"
PORT = 5000
WINDOW_TITLE = "Ship Crew Optimizer"
WINDOW_SIZE = (1600, 1000)


def get_api_url() -> str:
    """Return the full API base URL."""
    return f"http://{HOST}:{PORT}"


def _run_flask(thread_stop_event: threading.Event):
    """Run Flask in a thread that can be stopped gracefully.
    
    Args:
        thread_stop_event: Event to signal when to stop the server.
    """
    flask_app.run(
        host=HOST,
        port=PORT,
        debug=False,
        use_reloader=False,  # Prevent double-fork with threading
        threaded=True,
    )
    # Flask server exits; thread ends automatically


def _create_api_blueprint():
    """Create a simple HTML frontend placeholder for Phase 3.
    
    The full UI will be delivered in Phase 4.
    """
    html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Ship Crew Optimizer</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
            background: #1a1a2e;
            color: #e0e0e0;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
        }
        .container {
            text-align: center;
            padding: 40px;
            background: #16213e;
            border-radius: 12px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
            max-width: 600px;
        }
        h1 {
            color: #00d4ff;
            margin-bottom: 20px;
            font-size: 2em;
        }
        p {
            margin-bottom: 10px;
            font-size: 1.1em;
        }
        .status {
            margin-top: 20px;
            padding: 15px;
            background: #0f3460;
            border-radius: 8px;
            font-size: 0.95em;
        }
        .version {
            margin-top: 30px;
            font-size: 0.85em;
            color: #888;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Ship Crew Optimizer</h1>
        <p>Phase 3: PyWebView Integration</p>
        <p>API Server: <strong id="api-url">Loading...</strong></p>
        <div class="status">
            Frontend UI will be available in Phase 4.<br>
            The API is running and ready for requests.
        </div>
        <div class="version">v1.0.0 - Phase 3</div>
    </div>
    <script>
        document.getElementById('api-url').textContent = window.location.origin;
    </script>
</body>
</html>"""
    return flask.send_static_file


def create_app():
    """Create and configure the Flask application with HTML serving.
    
    Returns:
        Configured Flask app instance.
    """
    # Configure template folder
    current_dir = os.path.dirname(os.path.abspath(__file__))
    flask_app.template_folder = os.path.join(current_dir, 'templates')
    
    # Route to serve the Phase 4 frontend UI
    @flask_app.route("/")
    def index():
        return render_template('index.html')

    return flask_app


def create_window(api_url: str):
    """Create a PyWebView window.
    
    Args:
        api_url: The URL of the running Flask API server.
        
    Returns:
        Configured webview.Window instance.
    """
    return webview.create_window(
        title=WINDOW_TITLE,
        url=api_url,
        width=WINDOW_SIZE[0],
        height=WINDOW_SIZE[1],
        resizable=True,
        js_api=None,  # Expose API in Phase 4
    )


def shutdown_server(e: threading.Event):
    """Shutdown callback for PyWebView window close.
    
    Args:
        e: Event to set when window is closed.
    """
    e.set()
    # Get the Flask server thread and join it
    for thread in threading.enumerate():
        if thread.name == "flask_server":
            thread.join(timeout=2.0)


def main():
    """Main entry point for the desktop application."""
    # Ensure data files exist (create sample files if needed)
    if not os.path.exists(ROSTER_FILE):
        print(f"Creating sample roster file: {ROSTER_FILE}")
        # Create sample roster if it doesn't exist
        from models import Roster
        sample_roster = Roster()
        sample_roster.save_to_file(ROSTER_FILE)

    if not os.path.exists(SHIP_CONFIG_FILE):
        print(f"Creating sample ship config file: {SHIP_CONFIG_FILE}")
        from models import ShipConfig
        sample_config = ShipConfig()
        sample_config.save_to_file(SHIP_CONFIG_FILE)

    # Create Flask app
    flask_app = create_app()

    # Create stop event
    stop_event = threading.Event()

    # Start Flask server in background thread
    flask_thread = threading.Thread(
        target=flask_app.run,
        kwargs={
            "host": HOST,
            "port": PORT,
            "debug": False,
            "use_reloader": False,
            "threaded": True,
        },
        daemon=True,
        name="flask_server",
    )
    flask_thread.start()

    # Wait for server to start
    import time
    time.sleep(1)

    print(f"Flask server started on {get_api_url()}")

    # API URL for PyWebView
    api_url = get_api_url()

    # Create and start PyWebView window
    # Create and start PyWebView window
    try:
        # Create window object first
        window = webview.create_window(
            title=WINDOW_TITLE,
            url=api_url,
            width=WINDOW_SIZE[0],
            height=WINDOW_SIZE[1],
            resizable=True,
            js_api=None,  # Expose API in Phase 4
        )
        
        # Start webview with the window object
        webview.start()
    except Exception as e:
        print(f"Error starting PyWebView: {e}")
        print("Falling back to system browser...")
        import webbrowser
        webbrowser.open(api_url)
        print("Press Enter to exit...")
        input()
    finally:
        # Signal server to stop
        stop_event.set()
        print("\nShutting down server...")
        flask_thread.join(timeout=2.0)
        print("Server stopped.")


if __name__ == "__main__":
    main()
