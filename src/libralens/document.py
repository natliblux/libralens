from .record import Record
from .funcs import normalize_text

class Document:

    def __init__(
        self,
        eval: Record,
        gold: Record | None = None,
        platinum: Record | None = None,
        text: str | None = None
    ):

        self.eval = eval
        self.gold = gold
        self.platinum = platinum
        self.text = text
        self.text_normalized = (normalize_text(text) if text is not None else None)