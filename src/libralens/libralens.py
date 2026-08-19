from pathlib import Path
from .constants import RELEVANT_FIELDS
from .loader import load_data

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
        self.methods = methods
        self.fields = fields or list(RELEVANT_FIELDS.keys())
        self.gold = gold
        self.platinum = platinum
        self.text = text
        self.verbose = verbose

        self._validate_methods()
        self._validate_fields()

        self.data = load_data(self.eval, self.gold, self.platinum, self.text)

    def run(self):

        if self.verbose:
            self._print_info()

        return self.data

    def _print_info(self) -> None:

        records = "record" if len(self.data) == 1 else "records"
        types = ["eval"]
        if self.gold:
            types.append("gold")
        if self.platinum:
            types.append("platinum")
        if self.text:
            types.append("text")
        print(f"loaded {len(self.data)} {records}: {", ".join(types)}")
        print(f"running methods: {", ".join(self.methods)}")
        print(f"considering fields: {", ".join(self.fields)}")

    def _validate_methods(self):

        if not self.methods:
            raise ValueError("at least one method must be provided")

        # invalid = [method for method in self.methods if method not in AVAILABLE_METHODS]
        # if invalid:
        #     raise ValueError(...)

    def _validate_fields(self):

        invalid = [field for field in self.fields if field not in RELEVANT_FIELDS]
        if invalid:
            raise ValueError(f"unsupported fields: {', '.join(invalid)}")