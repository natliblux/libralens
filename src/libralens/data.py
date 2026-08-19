from .record import Record

class Data:

    def __init__(
        self,
        record: Record,
        gold: Record | None = None,
        platinum: Record | None = None,
        text: str | None = None
    ):

        self.record = record
        self.gold = gold
        self.platinum = platinum
        self.text = text