import socket
import threading
import webbrowser
from pathlib import Path
import uvicorn
from .server import create_app

def launch(output: str | Path, host: str = "127.0.0.1", open_browser: bool = True) -> None:

    app = create_app(output)

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind((host, 0))
        port = sock.getsockname()[1]

    if open_browser:
        threading.Timer(1.0, lambda: webbrowser.open(f"http://{host}:{port}")).start()

    uvicorn.run(app, host=host, port=port)