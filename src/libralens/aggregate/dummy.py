def aggregate(scores: dict):

    values = [score for score in scores.values() if score is not None]
    return sum(values) / len(values) if values else None