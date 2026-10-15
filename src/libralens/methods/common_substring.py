from difflib import SequenceMatcher
from .value_comparison import ValueComparisonMethod

class CommonSubstringMethod(ValueComparisonMethod):

    name = "common-substring"

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

        if not eval_text and not reference_text:
            return 1.0

        match = SequenceMatcher(None, eval_text, reference_text, autojunk=False).find_longest_match(0, len(eval_text), 0, len(reference_text))
        return 2 * match.size / (len(eval_text) + len(reference_text))