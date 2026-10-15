from Levenshtein import ratio
from .value_comparison import ValueComparisonMethod

class EditDistanceMethod(ValueComparisonMethod):

    name = "edit-distance"

    supported_fields = {
        "100": ("a", "b"),
        "110": ("a", "b"),
        "245": ("a", "b", "c", "d"),
        "264": ("a", "b", "c"),
        "490": ("a",),
        "700": ("a", "b"),
        "710": ("a", "b")
    }

    def compare_strings(self, eval_text: str, reference_text: str) -> float:
        return ratio(eval_text, reference_text)