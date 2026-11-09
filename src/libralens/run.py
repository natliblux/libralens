import json
from pathlib import Path
from dataclasses import dataclass

@dataclass
class Run:
    id: str
    method: str
    fields: list[str] | None = None

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

    if not isinstance(data, list):
        raise ValueError("runs json must contain a list")

    runs = []
    ids = set()

    for run in data:

        if not isinstance(run, dict):
            raise ValueError("each run must be an object")
        if "id" not in run:
            raise ValueError("each run must contain 'id'")
        if "method" not in run:
            raise ValueError("each run must contain 'method'")

        run_id = run["id"]
        fields = run.get("fields")

        if not isinstance(run_id, str) or not run_id.strip():
            raise ValueError("run 'id' must be a nonempty string")
        if run_id in ids:
            raise ValueError(f"duplicate run id: {run_id}")
        if fields is not None and not isinstance(fields, list):
            raise ValueError("'fields' must be a list")

        ids.add(run_id)
        runs.append(Run(id=run_id, method=run["method"], fields=fields))

    return runs