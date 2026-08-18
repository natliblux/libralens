from pathlib import Path
from .constants import RELEVANT_FIELDS
from .loader import load_data

class LibraLens:

    def __init__(self, eval: str | Path, tools: list[str], gold: str | Path | None = None, platinum: str | Path | None = None, fields: list[str] | None = None, verbose: bool = False):
        
        self.eval = eval
        self.gold = gold
        self.platinum = platinum
        self.tools = tools
        self.fields = fields
        if not self.fields:
            self.fields = list(RELEVANT_FIELDS.keys())
        self.verbose = verbose
        self.data = load_data(self.eval, self.gold, self.platinum)

        self._validate_tools()
        self._validate_fields()

    def run(self):

        if self.verbose:
            self._print_info()

        return self.data

    def _print_info(self) -> None:

        records = "records"
        if len(self.data) == 1:
            records = "record"
        types = ["eval"]
        if self.gold:
            types.append("gold")
        if self.platinum:
            types.append("platinum")
        print(f"loaded {len(self.data)} {records}: {", ".join(types)}")
        print(f"running tools: {", ".join(self.tools)}")
        print(f"considering fields: {", ".join(self.fields)}")

    def _validate_tools(self):

        if not self.tools:
            raise ValueError("at least one tool must be provided")

        # invalid = [tool for tool in self.tools if tool not in AVAILABLE_TOOLS]
        # if invalid:
        #     raise ValueError(...)

    def _validate_fields(self):

        if self.fields == ["*"]:
            return

        invalid = [field for field in self.fields if field not in RELEVANT_FIELDS]

        if invalid:
            raise ValueError(f"unsupported fields: {', '.join(invalid)}")