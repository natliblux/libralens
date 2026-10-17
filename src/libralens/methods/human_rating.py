from .base import BaseMethod

class HumanRatingMethod(BaseMethod):

    name = "human-rating"

    requires_pdf = True
    requires_output = True
    deferred = True

    supported_fields = {
        "008": ("00-05", "35-37"),
        "020": ("a",),
        "041": ("a",),
        "100": ("a", "b", "d", "0", "e", "4"),
        "110": ("a", "b", "d", "0", "e", "4"),
        "245": ("a", "b", "c", "d"),
        "264": ("a", "b", "c"),
        "300": ("a", "b"),
        "490": ("a",),
        "700": ("a", "b", "d", "0", "e", "4"),
        "710": ("a", "b", "d", "0", "e", "4")
    }

    def run_doc(self, doc, fields, llm=None):
        raise NotImplementedError("human ratings are collected through a rating session")