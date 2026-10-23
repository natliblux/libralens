from pathlib import Path
from .record import Record
from .funcs import normalize_text
from .matching import create_mapping

class Document:

    def __init__(
        self,
        eval: Record,
        gold: Record | None = None,
        platinum: Record | None = None,
        text: str | None = None,
        pdf: Path | None = None
    ):

        self.eval = eval
        self.gold = gold
        self.platinum = platinum
        self.text = text
        self.pdf = pdf
        self.text_normalized = (normalize_text(text) if text is not None else None)
        self.eval_to_gold_mapping = (create_mapping(self.eval, self.gold) if self.gold is not None else {})
        self.eval_to_platinum_mapping = (create_mapping(self.eval, self.platinum) if self.platinum is not None else {})
        self.gold_to_platinum_mapping = (create_mapping(self.gold, self.platinum) if self.gold is not None and self.platinum is not None else {})