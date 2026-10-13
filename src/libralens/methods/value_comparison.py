from abc import abstractmethod
from ..constants import GROUPED_FIELDS
from .base import BaseMethod
from ..funcs import join_subfields

class ValueComparisonMethod(BaseMethod):

    supported_fields = {
        "100": ("a", "b"),
        "110": ("a", "b"),
        "245": ("a", "b", "c", "d"),
        "264": ("a", "b", "c"),
        "490": ("a",),
        "700": ("a", "b"),
        "710": ("a", "b")
    }

    requires_gold_or_platinum = True

    def run_doc(self, doc, fields, llm=None):

        scores = []
        info = {}

        references = [(doc.gold, doc.gold_mapping, "gold"), (doc.platinum, doc.platinum_mapping, "platinum")]

        for reference, mapping, name in references:
            if reference is None:
                continue
            result = self.compare_records(doc.eval, reference, mapping, fields)
            if result["score"] is not None:
                scores.append(result["score"])
            info[name] = result

        return {"score": sum(scores) / len(scores) if scores else None, "info": info}

    def compare_records(self, eval_record, reference_record, mapping, fields) -> dict:

        comparisons = []

        grouped_fields = GROUPED_FIELDS & set(fields)

        if grouped_fields:
            self.compare_mapped_names(
                eval_record,
                reference_record,
                mapping,
                fields,
                grouped_fields,
                comparisons
            )

        if "245" in fields:
            self.compare_245(eval_record, reference_record, fields["245"], comparisons)

        if "264" in fields:
            self.compare_264(eval_record, reference_record, mapping, fields["264"], comparisons)

        if "490" in fields:
            self.compare_490(eval_record, reference_record, fields["490"], comparisons)

        scores = [comparison["score"] for comparison in comparisons]

        return {
            "score": sum(scores) / len(scores) if scores else None,
            "comparisons": comparisons,
        }

    def compare_mapped_names(self, eval_record, reference_record, mapping, fields, tags, comparisons) -> None:

        for eval_field in eval_record.fields:

            tag = eval_field["tag"]
            if tag not in tags:
                continue
            if not fields[tag] & {"a", "b"}:
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
                "eval_field": tag,
                "reference_field": reference_field["tag"],
                "sub_fields": ["a", "b"],
                "eval_text": eval_text,
                "reference_text": reference_text,
                "score": self.compare_strings(eval_text, reference_text),
            })

    def compare_264(self, eval_record, reference_record, mapping, sub_fields, comparisons) -> None:

        for eval_field in eval_record.fields:

            if eval_field["tag"] != "264":
                continue

            eval_id = eval_field["id"]
            if eval_id not in mapping:
                continue

            reference_field = reference_record.fields[mapping[eval_id]]
            if reference_field["tag"] != "264":
                continue

            for code in ["a", "b", "c"]:

                if code not in sub_fields:
                    continue

                eval_text = self.get_subfield(eval_field, code)
                reference_text = self.get_subfield(reference_field, code)

                if eval_text is None or reference_text is None:
                    continue

                comparisons.append({
                    "eval_field": "264",
                    "reference_field": "264",
                    "sub_fields": [code],
                    "eval_text": eval_text,
                    "reference_text": reference_text,
                    "score": self.compare_strings(eval_text, reference_text),
                })

    def compare_490(self, eval_record, reference_record, sub_fields, comparisons) -> None:

        if "a" not in sub_fields:
            return

        eval_field = self.get_field(eval_record, "490")
        reference_field = self.get_field(reference_record, "490")

        if eval_field is None or reference_field is None:
            return

        eval_text = self.get_subfield(eval_field, "a")
        reference_text = self.get_subfield(reference_field, "a")

        if eval_text is None or reference_text is None:
            return

        comparisons.append({
            "eval_field": "490",
            "reference_field": "490",
            "sub_fields": ["a"],
            "eval_text": eval_text,
            "reference_text": reference_text,
            "score": self.compare_strings(eval_text, reference_text),
        })

    def compare_245(self, eval_record, reference_record, sub_fields, comparisons) -> None:

        eval_field = self.get_field(eval_record, "245")
        reference_field = self.get_field(reference_record, "245")

        if eval_field is None or reference_field is None:
            return

        for code in ["a", "b", "c", "d"]:

            if code not in sub_fields:
                continue

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
                "score": self.compare_strings(eval_text, reference_text),
            })

        if {"a", "b"} <= sub_fields:

            eval_text = join_subfields(eval_field, {"a", "b"})
            reference_text = join_subfields(reference_field, {"a", "b"})

            if eval_text and reference_text:
                comparisons.append({
                    "eval_field": "245",
                    "reference_field": "245",
                    "sub_fields": ["a", "b"],
                    "eval_text": eval_text,
                    "reference_text": reference_text,
                    "score": self.compare_strings(eval_text, reference_text),
                })

    @abstractmethod
    def compare_strings(self, eval_text: str, reference_text: str) -> float:
        pass

    @staticmethod
    def get_field(record, tag: str) -> dict | None:
        return next((field for field in record.fields if field["tag"] == tag), None)

    @staticmethod
    def get_subfield(field: dict, code: str) -> str | None:
        return next((subfield["value"] for subfield in field["subfields"] if subfield["code"] == code), None)