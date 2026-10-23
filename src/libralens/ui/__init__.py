import threading
import webbrowser
from pathlib import Path
import uvicorn
from .server import create_app
from ..constants import HUMAN_RATING_PORT

def launch(output: str | Path) -> None:

    app = create_app(output)

    def open_browser():
        try:
            webbrowser.open(f"http://127.0.0.1:{HUMAN_RATING_PORT}")
        except Exception:
            pass

    threading.Timer(1.0, open_browser).start()
    uvicorn.run(app, host="127.0.0.1", port=HUMAN_RATING_PORT)