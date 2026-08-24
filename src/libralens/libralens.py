from pathlib import Path
import json
from .constants import RELEVANT_FIELDS
from .methods import METHODS
from .loader import load_documents
from .llm import LLM

class LibraLens:

    def __init__(
        self,
        eval: str | Path,
        methods: list[str],
        fields: list[str] | None = None,
        gold: str | Path | None = None,
        platinum: str | Path | None = None,
        text: str | Path | None = None,
        verbose: bool = False
    ):

        self.eval = eval
        self.methods = list(dict.fromkeys(methods))
        self.fields = (list(RELEVANT_FIELDS.keys()) if fields is None else fields)
        self.gold = gold
        self.platinum = platinum
        self.text = text
        self.verbose = verbose

        self._validate_methods()
        self._validate_fields()
        self.method_instances = [METHODS[name]() for name in self.methods]
        self._validate_requirements()
        self.llm = (LLM() if any(method.requires_llm for method in self.method_instances) else None)
        self.documents = load_documents(self.eval, self.gold, self.platinum, self.text, self.fields)

        self.score = None
        self.method_scores = {}
        self.document_scores = []
        self.results = []

    def run(self) -> list[dict]:

        if self.verbose:
            self._print_info()

        self.results = [{"methods": {}} for _ in self.documents]

        for method in self.method_instances:
            method_results = method.run(
                docs=self.documents,
                llm=self.llm
            )

            for i, result in enumerate(method_results):
                self.results[i]["methods"][method.name] = result
        self._compute_scores()

        if self.verbose:
            self._print_results()

        return self.results

    def _compute_scores(self) -> None:

        # per-document scores
        self.document_scores = []

        for result in self.results:

            scores = [method_result["score"] for method_result in result["methods"].values()]
            document_score = sum(scores) / len(scores)
            result["score"] = document_score
            self.document_scores.append(document_score)

        # Per-method scores
        self.method_scores = {}

        for method in self.methods:
            scores = [result["methods"][method]["score"] for result in self.results]
            self.method_scores[method] = sum(scores) / len(scores)

        # Overall score
        self.score = (
            sum(self.document_scores) / len(self.document_scores)
            if self.document_scores
            else None
        )

    def _print_info(self) -> None:

        documents_str = "document" if len(self.documents) == 1 else "documents"
        methods_str = "method" if len(self.methods) == 1 else "methods"
        fields_str = "field" if len(self.fields) == 1 else "fields"
        types = ["eval"]
        if self.gold is not None:
            types.append("gold")
        if self.platinum is not None:
            types.append("platinum")
        if self.text is not None:
            types.append("text")
        labels = [
            f"{len(self.documents)} {documents_str}",
            f"{len(self.methods)} {methods_str}",
            f"{len(self.fields)} {fields_str}",
        ]
        width = max(len(label) for label in labels)
        print(f"{labels[0]:<{width}} - {', '.join(types)}")
        print(f"{labels[1]:<{width}} - {', '.join(self.methods)}")
        print(f"{labels[2]:<{width}} - {', '.join(self.fields)}")
        print()

    def _print_results(self) -> None:

        print("document scores")
        for i, score in enumerate(self.document_scores):
            print(f"  {score:.3f} document {i}")
        print()
        print("method scores")
        for method, score in self.method_scores.items():
            print(f"  {score:.3f} {method}")
        print()
        print("dataset score")
        print(f"  {self.score:.3f} overall")

    def _validate_methods(self) -> None:

        if not self.methods:
            raise ValueError("at least one method must be provided")
        invalid = [method for method in self.methods if method not in METHODS]
        if invalid:
            raise ValueError(f"unsupported methods: {', '.join(invalid)}")

    def _validate_fields(self) -> None:

        invalid = [field for field in self.fields if field not in RELEVANT_FIELDS]
        if invalid:
            raise ValueError(f"unsupported fields: {', '.join(invalid)}")

    def _validate_requirements(self) -> None:

        for method in self.method_instances:
            if method.requires_gold and self.gold is None:
                raise ValueError(f"method '{method.name}' requires gold records")
            if method.requires_platinum and self.platinum is None:
                raise ValueError(f"method '{method.name}' requires platinum records")
            if method.requires_gold_or_platinum and self.gold is None and self.platinum is None:
                raise ValueError(f"method '{method.name}' requires gold or platinum records")
            if method.requires_text and self.text is None:
                raise ValueError(f"method '{method.name}' requires plain text")