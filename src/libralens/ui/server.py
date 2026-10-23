import json
from ..constants import HUMAN_RATINGS
from ..document import Document
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from ..rating import RatingSession
from ..record import Record
from ..enums import InputFormat

class RatingRequest(BaseModel):
    rating: str | None = None
    fields: dict = {}

def create_app(output: Path) -> FastAPI:

    output = Path(output).resolve()
    session = RatingSession(output)

    if not (output / "session.json").is_file():
        raise FileNotFoundError(f"rating session not found: {output}")

    app = FastAPI(title="LibraLens Human Rating")

    ui_dir = Path(__file__).parent
    app.mount("/static", StaticFiles(directory=ui_dir / "static"), name="static")
    @app.get("/", response_class=HTMLResponse)
    def index():
        return FileResponse(ui_dir / "templates" / "index.html")

    @app.get("/api/session")
    def get_session():

        config = json.loads((output / "session.json").read_text(encoding="utf-8"))
        ratings = session.load_ratings()

        completed = sum(doc["completed"] for doc in ratings["documents"].values())

        return {
            "config": config,
            "completed": completed,
            "total": config["n_documents"],
            "ratings": list(HUMAN_RATINGS),
            "initial_document": session.initial_document(),
            "selected_fields": session._get_selected_fields(),
        }

    @app.get("/api/documents/{document_id}")
    def get_document(document_id: int):

        config = json.loads((output / "session.json").read_text(encoding="utf-8"))
        n_documents = config["n_documents"]

        if document_id < 0 or document_id >= n_documents:
            raise HTTPException(status_code=404, detail="document not found")

        width = len(str(n_documents - 1))
        directory = output / "documents" / f"{document_id:0{width}d}"

        parsed = {}

        for name in ("eval", "gold", "platinum"):
            path = directory / f"{name}.xml"
            parsed[name] = Record(path.read_text(encoding="utf-8"), InputFormat.XML) if path.is_file() else None
        document = Document(eval=parsed["eval"], gold=parsed["gold"], platinum=parsed["platinum"])
        records = {name: record.fields if record is not None else None for name, record in parsed.items()}
        rows = session.build_rows(document)

        images = sorted((directory / "images").glob("*.png")) if (directory / "images").exists() else []

        ratings = session.load_ratings()

        return {
            "id": document_id,
            "records": records,
            "rows": rows,
            "images": [f"/api/documents/{document_id}/images/{path.name}" for path in images],
            "rating": ratings["documents"][str(document_id)]
        }

    @app.post("/api/documents/{document_id}")
    def save_document(document_id: int, request: RatingRequest):

        try:
            completed = session.save_document(document_id, request.model_dump())
        except ValueError as error:
            raise HTTPException(status_code=400, detail=str(error))

        return {"completed": completed}

    @app.get("/api/documents/{document_id}/images/{filename}")
    def get_image(document_id: int, filename: str):

        config = json.loads((output / "session.json").read_text(encoding="utf-8"))
        n_documents = config["n_documents"]

        if document_id < 0 or document_id >= n_documents:
            raise HTTPException(status_code=404, detail="document not found")

        width = len(str(n_documents - 1))
        path = output / "documents" / f"{document_id:0{width}d}" / "images" / filename

        if not path.is_file() or path.suffix.lower() != ".png":
            raise HTTPException(status_code=404, detail="image not found")

        return FileResponse(path, media_type="image/png")

    return app