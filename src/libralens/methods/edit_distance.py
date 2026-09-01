from Levenshtein import ratio
from .comparison import ComparisonMethod

class EditDistanceMethod(ComparisonMethod):

    name = "edit-distance"

    def compare_strings(self, eval_text: str, reference_text: str) -> float:
        return ratio(eval_text, reference_text)