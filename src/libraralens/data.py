from .record import Record

class Data:

    def __init__(self, record: Record, gold: Record | None = None):

        self.record = record
        self.gold = gold