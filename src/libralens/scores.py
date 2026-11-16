class Scores(dict):

    def __init__(self, runs: dict):

        super().__init__()

        for run_id, run in runs.items():
            if run.get("score") is not None:
                self[run_id] = run["score"]

            for reference, values in run.get("references", {}).items():
                prefix = f"{run_id}.{reference}"

                if values.get("score") is not None:
                    self[prefix] = values["score"]

                for field, field_values in values.items():
                    if field == "score":
                        continue

                    field_prefix = f"{prefix}.{field}"

                    for subfield, score in field_values.items():
                        key = field_prefix if subfield == "score" else f"{field_prefix}.{subfield}"
                        if score is not None:
                            self[key] = score

    def __missing__(self, key):
        return None