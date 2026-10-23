from pathlib import Path
from .ui import launch
from .run import Run
import shutil
from .funcs import record_to_xml, extract_pdf_images, compute_scores
import json
from .constants import FIELD_GROUPS, HUMAN_RATING_PORT
from .methods import METHODS
from .loader import load_documents
from .plot import create_results_plot
from .rating import RatingSession
from .llm import LLM, is_configured

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
        pdf: str | Path | None = None,
        output: str | Path | None = None,
        verbose: bool = False
    ):

        self.eval = eval
        self.gold = gold
        self.platinum = platinum
        self.text = text
        self.pdf = pdf
        self.output = Path(output) if output is not None else None
        self.verbose = verbose

        self._validate_output()

        if methods is not None and runs is not None:
            raise ValueError("provide either methods or runs, not both")

        if runs is not None and fields is not None:
            raise ValueError("fields cannot be provided when runs are used")

        if runs is not None:
            self.runs = [
                Run(
                    method=run.method,
                    fields=run.fields
                )
                for run in runs
            ]
        else:
            if methods is None:
                methods = [name for name, cls in METHODS.items() if not self._missing_requirements(cls())]
            else:
                methods = list(dict.fromkeys(methods))
            self.runs = [
                Run(
                    method=method,
                    fields=fields
                )
                for method in methods
            ]

        self._validate_runs()
        for run in self.runs:
            run.fields = self._resolve_fields(run.fields, METHODS[run.method].supported_fields)
        self.methods = [run.method for run in self.runs]
        self.fields = list(dict.fromkeys(field for run in self.runs for field in run.fields))
        self.method_instances = {run.method: METHODS[run.method]() for run in self.runs}
        self._validate_requirements()
        self.llm = (LLM() if any(self.method_instances[run.method].requires_llm for run in self.runs) else None)
        self.documents = load_documents(self.eval, self.gold, self.platinum, self.text, self.pdf)
        self.score = None
        self.method_scores = {}
        self.document_scores = {}
        self.results = []

    def evaluate(self, open_ui: bool = True) -> None:

        if self.verbose:
            self._print_info()

        self.results = [{"id": i, "methods": {}} for i in range(len(self.documents))]

        method_width = max(len(run.method) for run in self.runs)

        for run in self.runs:

            method = self.method_instances[run.method]
            if method.deferred:
                continue

            method_results = method.run(docs=self.documents, fields=run.fields, llm=self.llm, verbose=self.verbose, desc=f"{run.method:<{method_width}}")
            for i, result in enumerate(method_results):
                self.results[i]["methods"][run.method] = result

        self._compute_scores()

        if self.output:
            self._write_output()
            if "human-rating" in self.methods:
                RatingSession(self.output).create(self.runs, len(self.documents))
                if open_ui:
                    self.annotate(self.output)
        if self.verbose:
            self._print_results()

        return self.results

    def _compute_scores(self) -> None:

        self.document_scores, self.method_scores, self.score = compute_scores(self.results, self.methods)

    def _format_fields(self, fields) -> str:

        values = []

        for field, subfields in fields.items():
            if not subfields:
                values.append(field)
            else:
                values.extend(f"{field}.{subfield}" for subfield in sorted(subfields))

        return ", ".join(values)

    def _print_info(self) -> None:

        documents_str = "document" if len(self.documents) == 1 else "documents"

        types = ["eval"]
        if self.gold is not None:
            types.append("gold")
        if self.platinum is not None:
            types.append("platinum")
        if self.text is not None:
            types.append("text")
        if self.pdf is not None:
            types.append("pdf")

        print(f"{len(self.documents)} {documents_str}")
        print(f"  {', '.join(types)}")
        print()

        for run in self.runs:
            print(run.method)
            print(f"  {self._format_fields(run.fields)}")
            print()

    def _print_results(self) -> None:

        print()
        print("document scores")
        for document_id, score in self.document_scores.items():
            score_str = f"{score:.3f}" if score is not None else f"{'n/a':>5}"
            print(f"  {score_str} document {document_id}")

        print()
        print("method scores")
        for method, score in self.method_scores.items():
            score_str = f"{score:.3f}" if score is not None else f"{'n/a':>5}"
            print(f"  {score_str} {method}")

        print()
        print("dataset score")
        score_str = f"{self.score:.3f}" if self.score is not None else f"{'n/a':>5}"
        print(f"  {score_str} overall")

    def _write_output(self) -> None:

        if self.output.exists():
            shutil.rmtree(self.output)
        self.output.mkdir(parents=True)
        documents_dir = self.output / "documents"
        documents_dir.mkdir(exist_ok=True)

        # detailed evaluation results
        results_file = self.output / "results.json"

        with results_file.open("w", encoding="utf-8") as file:
            json.dump(self.results, file, indent=4, ensure_ascii=False)

        # plot
        completed_methods = [method for method in self.methods if method in self.method_scores]
        create_results_plot(results=self.results, methods=completed_methods, overall_score=self.score, output_path=self.output / "results.png")

        # document data
        width = len(str(len(self.documents) - 1))
        for i, document in enumerate(self.documents):

            document_dir = documents_dir / f"{i:0{width}d}"
            document_dir.mkdir()

            (document_dir / "eval.xml").write_text(record_to_xml(document.eval), encoding="utf-8")
            if document.gold is not None:
                (document_dir / "gold.xml").write_text(record_to_xml(document.gold), encoding="utf-8")
            if document.platinum is not None:
                (document_dir / "platinum.xml").write_text(record_to_xml(document.platinum), encoding="utf-8")
            if document.text is not None:
                (document_dir / "text.txt").write_text(document.text, encoding="utf-8")
            if document.pdf is not None:
                images_dir = document_dir / "images"
                images_dir.mkdir()
                extract_pdf_images(document.pdf, images_dir)

    def _validate_output(self) -> None:

        if self.output is None:
            return

        if self.output.exists() and not self.output.is_dir():
            raise ValueError(f"output path is not a directory: {self.output}")

        if (self.output / "session.json").exists() or (self.output / "ratings.json").exists():
            raise ValueError(f"the following output directory cannot be overwritten: {self.output}")

    def _validate_requirements(self) -> None:

        for run in self.runs:
            method = self.method_instances[run.method]
            missing = self._missing_requirements(method)
            if missing:
                raise ValueError(f"method '{method.name}' requires: {', '.join(missing)}")

    def _validate_runs(self) -> None:

        if not self.runs:
            raise ValueError("at least one run must be provided")

        methods = [run.method for run in self.runs]

        if len(methods) != len(set(methods)):
            raise ValueError("each method can only be run once")

        invalid_methods = [method for method in methods if method not in METHODS]

        if invalid_methods:
            raise ValueError(f"unsupported methods: {', '.join(invalid_methods)}")

    def _resolve_fields(self, fields: list[str] | None, supported_fields: dict[str, tuple[str, ...]]) -> dict[str, set[str]]:

        if fields is None:
            return {field: set(subfields) for field, subfields in supported_fields.items()}

        resolved = {}

        for selector in fields:

            if "." in selector:
                field, subfield = selector.split(".", 1)
                if field not in supported_fields or subfield not in supported_fields[field]:
                    continue
                resolved.setdefault(field, set()).add(subfield)

            else:
                field = selector
                if field not in supported_fields:
                    continue
                resolved[field] = set(supported_fields[field])

        for group in FIELD_GROUPS:

            selected_subfields = set().union(*(resolved.get(field, set()) for field in group))

            if not selected_subfields:
                continue

            for field in group:
                if field not in supported_fields:
                    continue
                for subfield in selected_subfields:
                    if subfield in supported_fields[field]:
                        resolved.setdefault(field, set()).add(subfield)

        return resolved

    def _missing_requirements(self, method) -> list[str]:

        missing = []

        if method.requires_gold and self.gold is None:
            missing.append("gold records")
        if method.requires_platinum and self.platinum is None:
            missing.append("platinum records")
        if method.requires_gold_or_platinum and self.gold is None and self.platinum is None:
            missing.append("gold or platinum records")
        if method.requires_text and self.text is None:
            missing.append("plain text")
        if method.requires_pdf and self.pdf is None:
            missing.append("pdf documents")
        if method.requires_output and self.output is None:
            missing.append("output directory")
        if method.requires_llm and not is_configured():
            missing.append("llm configuration")

        return missing

    @staticmethod
    def annotate(output: str | Path) -> None:
        print(f"human-rating: open http://localhost:{HUMAN_RATING_PORT} in your browser")
        launch(output)