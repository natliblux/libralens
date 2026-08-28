import json
from pathlib import Path
from .run import Run

def load_runs(path: str | Path) -> list[Run]:

    path = Path(path)

    if not path.is_file():
        raise ValueError(f"runs file does not exist: {path}")
    if path.suffix.lower() != ".json":
        raise ValueError("runs file must use the .json extension")

    try:
        with path.open("r", encoding="utf-8") as file:
            data = json.load(file)
    except json.JSONDecodeError as e:
        raise ValueError(f"invalid json runs: {e}")

    if "runs" not in data:
        raise ValueError("json must contain 'runs'")
    if not isinstance(data["runs"], list):
        raise ValueError("'runs' must be a list")

    runs = []

    for run in data["runs"]:

        if not isinstance(run, dict):
            raise ValueError("each run must be an object")
        if "method" not in run:
            raise ValueError("each run must contain 'method'")

        fields = run.get("fields")

        if fields is not None and not isinstance(fields, list):
            raise ValueError("'fields' must be a list")

        runs.append(Run(method=run["method"], fields=fields))

    return runs