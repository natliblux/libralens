from .set_comparison import SetComparisonMethod

class RecallMethod(SetComparisonMethod):

    name = "recall-score"

    def calculate_score(self, tp, fp, fn) -> float | None:

        if tp + fn == 0:
            return None

        return tp / (tp + fn)