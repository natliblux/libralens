from .value_comparison import ValueComparisonMethod

class ExactMatchMethod(ValueComparisonMethod):

    name = "exact-match"
    combine_names = False

    supported_fields = {
        "008": ("00-05", "35-37"),
        "020": ("ind1", "ind2", "a"),
        "041": ("ind1", "ind2"),
        "100": ("ind1", "ind2", "d", "0", "e", "4"),
        "110": ("ind1", "ind2", "d", "0", "e", "4"),
        "245": ("ind1", "ind2"),
        "264": ("ind1", "ind2", "c"),
        "300": ("ind1", "ind2", "a", "b"),
        "490": ("ind1", "ind2"),
        "700": ("ind1", "ind2", "d", "0", "e", "4"),
        "710": ("ind1", "ind2", "d", "0", "e", "4")
    }

    def compare_strings(self, eval_text: str, reference_text: str) -> float:
        return float(eval_text == reference_text)