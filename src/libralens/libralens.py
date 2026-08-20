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

    def run(self):

        if self.verbose:
            self._print_info()

        results = [{} for _ in self.documents]

        for method in self.method_instances:
            method_results = method.run(
                docs=self.documents,
                llm=self.llm
            )

            for i, result in enumerate(method_results):
                results[i][method.name] = result

        if self.verbose:
            print(json.dumps(results, indent=4))

        return results

    def _print_info(self) -> None:

        documents = "document" if len(self.documents) == 1 else "documents"
        types = ["eval"]
        if self.gold is not None:
            types.append("gold")
        if self.platinum is not None:
            types.append("platinum")
        if self.text is not None:
            types.append("text")

        print(f"loaded {len(self.documents)} {documents}: {", ".join(types)}")
        print(f"running methods: {", ".join(self.methods)}")
        print(f"considering fields: {", ".join(self.fields)}")

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