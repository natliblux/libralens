from pathlib import Path
from .run import Run
import shutil
from .funcs import record_to_xml
import json
from .constants import RELEVANT_FIELDS
from .methods import METHODS
from .loader import load_documents
from .llm import LLM

class LibraLens:

    def __init__(
        self,
        eval: str | Path,
        methods: list[str] | None = None,
        fields: list[str] | None = None,
        runs: list[Run] | None = None,
        gold: str | Path | None = None,
        platinum: str | Path | None = None,
        text: str | Path | None = None,
        output: str | Path | None = None,
        verbose: bool = False
    ):

        self.eval = eval
        self.gold = gold
        self.platinum = platinum
        self.text = text
        self.output = Path(output) if output is not None else None
        self.verbose = verbose

        self._validate_output()

        if methods is not None and runs is not None:
            raise ValueError("provide either methods or runs, not both")
        if methods is None and runs is None:
            raise ValueError("methods or runs must be provided")
        if runs is not None and fields is not None:
            raise ValueError("fields cannot be provided when runs are used")

        if runs is not None:
            self.runs = [
                Run(
                    method=run.method,
                    fields=list(RELEVANT_FIELDS.keys()) if run.fields is None else list(dict.fromkeys(run.fields))
                )
                for run in runs
            ]
        else:
            methods = list(dict.fromkeys(methods))
            selected_fields = list(RELEVANT_FIELDS.keys()) if fields is None else list(dict.fromkeys(fields))
            self.runs = [Run(method=method, fields=list(selected_fields)) for method in methods]

        self._validate_runs()
        self.methods = [run.method for run in self.runs]
        self.fields = list(dict.fromkeys(field for run in self.runs for field in run.fields))
        self.method_instances = {run.method: METHODS[run.method]() for run in self.runs}
        self._validate_requirements()
        self.llm = (LLM() if any(self.method_instances[run.method].requires_llm for run in self.runs) else None)
        self.documents = load_documents(self.eval, self.gold, self.platinum, self.text)
        self.score = None
        self.method_scores = {}
        self.document_scores = {}
        self.results = []

    def run(self) -> list[dict]:

        if self.verbose:
            self._print_info()

        self.results = [
            {"id": i, "methods": {}}
            for i in range(len(self.documents))
        ]

        for run in self.runs:

            method = self.method_instances[run.method]

            method_results = method.run(docs=self.documents, fields=run.fields, llm=self.llm)

            for i, result in enumerate(method_results):
                self.results[i]["methods"][run.method] = result

        self._compute_scores()

        if self.output:
            self._write_results()
        if self.verbose:
            self._print_results()

        return self.results

    def _compute_scores(self) -> None:

        # per-document scores
        self.document_scores = {}

        for result in self.results:
            scores = [
                method_result["score"]
                for method_result in result["methods"].values()
                if method_result["score"] is not None
            ]

            document_score = sum(scores) / len(scores) if scores else None

            result["score"] = document_score
            self.document_scores[result["id"]] = document_score

        # per-method scores
        self.method_scores = {}

        for method in self.methods:
            scores = [
                result["methods"][method]["score"]
                for result in self.results
                if result["methods"][method]["score"] is not None
            ]

            self.method_scores[method] = sum(scores) / len(scores) if scores else None

        # overall score
        scores = [
            score
            for score in self.document_scores.values()
            if score is not None
        ]

        self.score = sum(scores) / len(scores) if scores else None

    def _print_info(self) -> None:

        documents_str = "document" if len(self.documents) == 1 else "documents"

        types = ["eval"]
        if self.gold is not None:
            types.append("gold")
        if self.platinum is not None:
            types.append("platinum")
        if self.text is not None:
            types.append("text")

        print(f"{len(self.documents)} {documents_str}")
        print(f"  {', '.join(types)}")
        print()

        for run in self.runs:
            print(run.method)
            print(f"  {', '.join(run.fields)}")
            print()

    def _print_results(self) -> None:

        print("document scores")
        for document_id, score in self.document_scores.items():
            print(f"  {score:.3f} document {document_id}")
        print()
        print("method scores")
        for method, score in self.method_scores.items():
            print(f"  {score:.3f} {method}")
        print()
        print("dataset score")
        print(f"  {self.score:.3f} overall")

    def _write_record(self, record, path: Path) -> None:
        path.write_text(record_to_xml(record), encoding="utf-8")

    def _write_results(self) -> None:

        if self.output.exists():
            shutil.rmtree(self.output)
        self.output.mkdir(parents=True)
        documents_dir = self.output / "documents"
        documents_dir.mkdir(exist_ok=True)

        # detailed evaluation results
        results_file = self.output / "results.json"

        with results_file.open("w", encoding="utf-8") as file:
            json.dump(self.results, file, indent=4, ensure_ascii=False)

        width = len(str(len(self.documents) - 1))

        # document data
        for i, document in enumerate(self.documents):

            document_dir = documents_dir / f"{i:0{width}d}"
            document_dir.mkdir()

            self._write_record(document.eval, document_dir / "eval.xml")

            if document.gold is not None:
                self._write_record(document.gold, document_dir / "gold.xml")

            if document.platinum is not None:
                self._write_record(document.platinum, document_dir / "platinum.xml")

            if document.text is not None:
                (document_dir / "text.txt").write_text(document.text, encoding="utf-8")

    def _validate_output(self) -> None:

        if self.output is not None and self.output.exists() and not self.output.is_dir():
            raise ValueError(f"output path is not a directory: {self.output}")

    def _validate_requirements(self) -> None:

        for run in self.runs:
            method = self.method_instances[run.method]

            if method.requires_gold and self.gold is None:
                raise ValueError(f"method '{method.name}' requires gold records")

            if method.requires_platinum and self.platinum is None:
                raise ValueError(f"method '{method.name}' requires platinum records")

            if method.requires_gold_or_platinum and self.gold is None and self.platinum is None:
                raise ValueError(f"method '{method.name}' requires gold or platinum records")

            if method.requires_text and self.text is None:
                raise ValueError(f"method '{method.name}' requires plain text")

    def _validate_runs(self) -> None:

        if not self.runs:
            raise ValueError("at least one run must be provided")

        methods = [run.method for run in self.runs]

        if len(methods) != len(set(methods)):
            raise ValueError("each method can only be run once")

        invalid_methods = [method for method in methods if method not in METHODS]

        if invalid_methods:
            raise ValueError(f"unsupported methods: {', '.join(invalid_methods)}")

        for run in self.runs:
            invalid_fields = [field for field in run.fields if field not in RELEVANT_FIELDS]
            if invalid_fields:
                raise ValueError(f"unsupported fields for method '{run.method}': {', '.join(invalid_fields)}")