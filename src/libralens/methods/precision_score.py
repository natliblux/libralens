from .set_comparison import SetComparisonMethod

class PrecisionMethod(SetComparisonMethod):

    name = "precision-score"

    def calculate_score(self, tp, fp, fn) -> float | None:

        if tp + fp == 0:
            return None

        return tp / (tp + fp)