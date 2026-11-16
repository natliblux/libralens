def aggregate(scores: dict) -> dict[str, float | None]:

    values = [score for score in scores.values() if score is not None]
    return {"quality": sum(values) / len(values) if values else None}