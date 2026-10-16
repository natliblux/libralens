import threading
import webbrowser
from pathlib import Path
import uvicorn
from .server import create_app

def launch(output: str | Path, host: str = "127.0.0.1", port: int = 8000, open_browser: bool = True) -> None:

    app = create_app(output)
    if open_browser:
        threading.Timer(1.0, lambda: webbrowser.open(f"http://{host}:{port}")).start()
    uvicorn.run(app, host=host, port=port)