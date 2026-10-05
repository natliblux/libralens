from .base import BaseMethod

class F1ScoreMethod(BaseMethod):

    name = "f1-score"
    supported_fields = {
        "041": ("a",),
        "100": ("0", "4"),
        "110": ("0", "4"),
        "700": ("0", "4"),
        "710": ("0", "4")
    }
    requires_gold_or_platinum = True

    def run_doc(self, doc, fields, llm=None):

        scores = []
        info = {}

        references = [(doc.gold, "gold"), (doc.platinum, "platinum")]

        for reference, name in references:
            if reference is None:
                continue
            result = self.compare_records(doc.eval, reference, fields)
            if result["score"] is not None:
                scores.append(result["score"])
            info[name] = result

        return {"score": sum(scores) / len(scores) if scores else None, "info": info}

    def compare_records(self, record, reference, fields) -> dict:

        comparisons = []

        if "041" in fields and "a" in fields["041"]:
            self.add_comparison(
                comparisons,
                fields=["041"],
                sub_fields=["a"],
                eval_values=record.lang_codes,
                reference_values=reference.lang_codes
            )

        people_tags = {"100", "700"} & fields.keys()

        relator_tags = {tag for tag in people_tags if "4" in fields[tag]}
        authority_tags = {tag for tag in people_tags if "0" in fields[tag]}

        if relator_tags:
            self.add_comparison(
                comparisons,
                fields=sorted(relator_tags),
                sub_fields=["4"],
                eval_values=self.get_values(record.relators, relator_tags),
                reference_values=self.get_values(reference.relators, relator_tags)
            )

        if authority_tags:
            self.add_comparison(
                comparisons,
                fields=sorted(authority_tags),
                sub_fields=["0"],
                eval_values=self.get_values(record.authorities, authority_tags),
                reference_values=self.get_values(reference.authorities, authority_tags)
            )

        company_tags = {"110", "710"} & fields.keys()

        relator_tags = {tag for tag in company_tags if "4" in fields[tag]}
        authority_tags = {tag for tag in company_tags if "0" in fields[tag]}

        if relator_tags:
            self.add_comparison(
                comparisons,
                fields=sorted(relator_tags),
                sub_fields=["4"],
                eval_values=self.get_values(record.relators, relator_tags),
                reference_values=self.get_values(reference.relators, relator_tags)
            )

        if authority_tags:
            self.add_comparison(
                comparisons,
                fields=sorted(authority_tags),
                sub_fields=["0"],
                eval_values=self.get_values(record.authorities, authority_tags),
                reference_values=self.get_values(reference.authorities, authority_tags)
            )

        scores = [comparison["score"] for comparison in comparisons]

        return {
            "score": sum(scores) / len(scores) if scores else None,
            "comparisons": comparisons,
        }

    def add_comparison(self, comparisons, fields, sub_fields, eval_values, reference_values) -> None:

        eval_values = set(eval_values)
        reference_values = set(reference_values)

        if not eval_values and not reference_values:
            return

        true_positives = eval_values & reference_values
        false_positives = eval_values - reference_values
        false_negatives = reference_values - eval_values

        tp = len(true_positives)
        fp = len(false_positives)
        fn = len(false_negatives)

        precision = tp / (tp + fp) if tp + fp else 0.0
        recall = tp / (tp + fn) if tp + fn else 0.0
        score = 2 * tp / (2 * tp + fp + fn)

        comparisons.append({
            "fields": fields,
            "sub_fields": sub_fields,
            "eval": sorted(eval_values),
            "reference": sorted(reference_values),
            "true_positives": sorted(true_positives),
            "false_positives": sorted(false_positives),
            "false_negatives": sorted(false_negatives),
            "precision": precision,
            "recall": recall,
            "score": score,
        })

    @staticmethod
    def get_values(values, tags) -> list[str]:
        return [value for tag in tags for value in values[tag]]