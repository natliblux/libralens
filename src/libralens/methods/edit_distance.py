from Levenshtein import ratio
from .value_comparison import ValueComparisonMethod

class EditDistanceMethod(ValueComparisonMethod):

    name = "edit-distance"

    def compare_strings(self, eval_text: str, reference_text: str) -> float:
        return ratio(eval_text, reference_text)