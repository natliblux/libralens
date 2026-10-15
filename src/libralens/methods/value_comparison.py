from abc import abstractmethod
from ..constants import GROUPED_FIELDS
from .base import BaseMethod
from ..funcs import join_subfields

class ValueComparisonMethod(BaseMethod):

    requires_gold_or_platinum = True
    combine_names = True

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

        for tag, sub_fields in fields.items():

            if tag in GROUPED_FIELDS:
                continue

            if tag == "264":
                self.compare_mapped_fields(eval_record, reference_record, mapping, {tag}, sub_fields, comparisons)
            else:
                self.compare_standard_field(eval_record, reference_record, tag, sub_fields, comparisons)

        grouped_fields = GROUPED_FIELDS & set(fields)

        if grouped_fields:
            self.compare_mapped_fields(eval_record, reference_record, mapping, grouped_fields, fields, comparisons)

        scores = [comparison["score"] for comparison in comparisons]

        return {
            "score": sum(scores) / len(scores) if scores else None,
            "comparisons": comparisons,
        }

    def compare_standard_field(self, eval_record, reference_record, tag, sub_fields, comparisons) -> None:

        eval_field = self.get_field(eval_record, tag)
        reference_field = self.get_field(reference_record, tag)

        if eval_field is None or reference_field is None:
            return

        for code in sub_fields:
            self.compare_subfield(eval_field, reference_field, code, comparisons)

        if self.combine_names and tag == "245" and {"a", "b"} <= sub_fields:
            self.compare_combined(eval_field, reference_field, comparisons)

    def compare_mapped_fields(self, eval_record, reference_record, mapping, tags, sub_fields, comparisons) -> None:

        for eval_field in eval_record.fields:

            tag = eval_field["tag"]

            if tag not in tags:
                continue

            eval_id = eval_field["id"]

            if eval_id not in mapping:
                continue

            reference_field = reference_record.fields[mapping[eval_id]]

            if reference_field["tag"] not in tags:
                continue

            if tag in GROUPED_FIELDS:
                selected = sub_fields[tag]

                if self.combine_names:
                    if selected & {"a", "b"}:
                        self.compare_combined(eval_field, reference_field, comparisons)
                else:
                    for code in selected:
                        self.compare_subfield(eval_field, reference_field, code, comparisons)

            else:
                for code in sub_fields:
                    self.compare_subfield(eval_field, reference_field, code, comparisons)

    def compare_subfield(self, eval_field, reference_field, code, comparisons) -> None:

        eval_text = self.get_subfield(eval_field, code)
        reference_text = self.get_subfield(reference_field, code)

        if eval_text is None or reference_text is None:
            return

        comparisons.append({
            "eval_field": eval_field["tag"],
            "reference_field": reference_field["tag"],
            "sub_fields": [code],
            "eval_text": eval_text,
            "reference_text": reference_text,
            "score": self.compare_strings(eval_text, reference_text),
        })

    def compare_combined(self, eval_field, reference_field, comparisons) -> None:

        eval_text = join_subfields(eval_field, {"a", "b"})
        reference_text = join_subfields(reference_field, {"a", "b"})

        if not eval_text or not reference_text:
            return

        comparisons.append({
            "eval_field": eval_field["tag"],
            "reference_field": reference_field["tag"],
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