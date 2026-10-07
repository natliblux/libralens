from .set_comparison import SetComparisonMethod

class F1ScoreMethod(SetComparisonMethod):

    name = "f1-score"

    def calculate_score(self, tp, fp, fn) -> float:
        return 2 * tp / (2 * tp + fp + fn)