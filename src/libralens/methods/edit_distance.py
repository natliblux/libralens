from Levenshtein import ratio
from .base import BaseMethod
from ..funcs import join_subfields

class EditDistanceMethod(BaseMethod):

    name = "edit-distance"
    requires_gold_or_platinum = True

    def run_doc(self, doc, llm=None):

        scores = []
        info = {}

        references = [
            (doc.gold, doc.gold_mapping, "gold"),
            (doc.platinum, doc.platinum_mapping, "platinum"),
        ]

        for reference, mapping, name in references:

            if reference is None:
                continue

            result = self.compare_records(
                doc.eval,
                reference,
                mapping,
            )

            if result["score"] is not None:
                scores.append(result["score"])

            info[name] = result

        return {
            "score": sum(scores) / len(scores) if scores else None,
            "info": info,
        }

    def compare_records(self, eval_record, reference_record, mapping) -> dict:

        comparisons = []

        self.compare_mapped_names(eval_record, reference_record, mapping, comparisons)
        self.compare_245(eval_record, reference_record, comparisons)

        scores = [comparison["score"] for comparison in comparisons]

        return {
            "score": sum(scores) / len(scores) if scores else None,
            "comparisons": comparisons,
        }

    def compare_mapped_names(self, eval_record, reference_record, mapping, comparisons) -> None:

        tags = {"100", "110", "700", "710"}

        for eval_field in eval_record.fields:

            if eval_field["tag"] not in tags:
                continue

            eval_id = eval_field["id"]

            if eval_id not in mapping:
                continue

            reference_field = reference_record.fields[mapping[eval_id]]
            eval_text = join_subfields(eval_field, {"a", "b"})
            reference_text = join_subfields(reference_field, {"a", "b"})

            if not eval_text or not reference_text:
                continue

            comparisons.append({
                "eval_field": eval_field["tag"],
                "reference_field": reference_field["tag"],
                "sub_fields": ["a", "b"],
                "eval_text": eval_text,
                "reference_text": reference_text,
                "score": ratio(
                    eval_text,
                    reference_text,
                ),
            })

    def compare_245(self, eval_record, reference_record, comparisons) -> None:

        eval_field = self.get_field(eval_record, "245")
        reference_field = self.get_field(reference_record, "245")

        if eval_field is None or reference_field is None:
            return

        for code in ["a", "b", "c", "d"]:

            eval_text = self.get_subfield(eval_field, code)
            reference_text = self.get_subfield(reference_field, code)

            if eval_text is None or reference_text is None:
                continue

            comparisons.append({
                "eval_field": "245",
                "reference_field": "245",
                "sub_fields": [code],
                "eval_text": eval_text,
                "reference_text": reference_text,
                "score": ratio(eval_text, reference_text),
            })

        eval_text = join_subfields(eval_field, {"a", "b"})
        reference_text = join_subfields(reference_field, {"a", "b"})

        if eval_text and reference_text:
            comparisons.append({
                "eval_field": "245",
                "reference_field": "245",
                "sub_fields": ["a", "b"],
                "eval_text": eval_text,
                "reference_text": reference_text,
                "score": ratio(eval_text, reference_text),
            })

    @staticmethod
    def get_field(record, tag: str) -> dict | None:
        return next((field for field in record.fields if field["tag"] == tag), None)

    @staticmethod
    def get_subfield(field: dict, code: str) -> str | None:
        return next((subfield["value"] for subfield in field["subfields"] if subfield["code"] == code), None)