from .value_comparison import ValueComparisonMethod

class ExactMatchMethod(ValueComparisonMethod):

    name = "exact-match"
    combine_names = False

    supported_fields = {
        "008": ("00-05", "35-37"),
        "020": ("a",),
        "100": ("d", "0", "e", "4"),
        "110": ("d", "0", "e", "4"),
        "264": ("c",),
        "300": ("a", "b"),
        "700": ("d", "0", "e", "4"),
        "710": ("d", "0", "e", "4")
    }

    def compare_strings(self, eval_text: str, reference_text: str) -> float:
        return float(eval_text == reference_text)