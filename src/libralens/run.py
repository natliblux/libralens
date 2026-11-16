import json
from pathlib import Path
from dataclasses import dataclass

@dataclass
class Run:
    method: str
    id: str | None = None
    fields: list[str] | None = None

    def __post_init__(self):
        if self.id is None:
            self.id = self.method

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
        if "method" not in run:
            raise ValueError("each run must contain 'method'")

        method = run["method"]
        run_id = run.get("id", method)
        fields = run.get("fields")

        if not isinstance(method, str) or not method.strip():
            raise ValueError("run 'method' must be a nonempty string")
        if not isinstance(run_id, str) or not run_id.strip():
            raise ValueError("run 'id' must be a nonempty string")
        if run_id in ids:
            raise ValueError(f"duplicate run id: {run_id}")
        if fields is not None and not isinstance(fields, list):
            raise ValueError("'fields' must be a list")

        ids.add(run_id)
        runs.append(Run(id=run_id, method=method, fields=fields))

    return runs