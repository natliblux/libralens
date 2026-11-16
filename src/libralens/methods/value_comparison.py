from abc import abstractmethod
from ..constants import FIELD_GROUPS, GROUPED_FIELDS
from .base import BaseMethod
from ..funcs import join_subfields

class ValueComparisonMethod(BaseMethod):

    requires_reference = True
    combine_subfields = True

    def run_doc(self, doc, fields, llm=None):

        scores = []
        info = {}
        references = {}

        sources = [(doc.gold, doc.eval_to_gold_mapping, "gold"), (doc.platinum, doc.eval_to_platinum_mapping, "platinum")]

        for reference, mapping, name in sources:
            if reference is None:
                continue

            result = self.compare_records(doc.eval, reference, mapping, fields, llm)

            if result["score"] is not None:
                scores.append(result["score"])
                references[name] = {
                    "score": result["score"],
                    **self.build_field_scores(result["comparisons"])
                }

            info[name] = result

        return {
            "score": sum(scores) / len(scores) if scores else None,
            "references": references,
            "info": info
        }

    def compare_records(self, eval_record, reference_record, mapping, fields, llm=None) -> dict:

        comparisons = []

        for tag, sub_fields in fields.items():

            if tag in GROUPED_FIELDS:
                continue

            if tag == "264":
                self.compare_mapped_fields(eval_record, reference_record, mapping, {tag}, sub_fields, comparisons, llm)
            else:
                self.compare_standard_field(eval_record, reference_record, tag, sub_fields, comparisons, llm)

        grouped_fields = GROUPED_FIELDS & set(fields)

        if grouped_fields:
            self.compare_mapped_fields(eval_record, reference_record, mapping, grouped_fields, fields, comparisons, llm)

        scores = [comparison["score"] for comparison in comparisons]

        return {
            "score": sum(scores) / len(scores) if scores else None,
            "comparisons": comparisons,
        }

    def compare_standard_field(self, eval_record, reference_record, tag, sub_fields, comparisons, llm=None) -> None:

        eval_field = self.get_field(eval_record, tag)
        reference_field = self.get_field(reference_record, tag)

        if eval_field is None or reference_field is None:
            return

        for code in sub_fields:
            self.compare_subfield(eval_field, reference_field, code, comparisons, llm)

        if self.combine_subfields and tag == "245" and {"a", "b"} <= sub_fields:
            self.compare_combined(eval_field, reference_field, comparisons, llm)

    def compare_mapped_fields(self, eval_record, reference_record, mapping, tags, sub_fields, comparisons, llm=None) -> None:

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

                if self.combine_subfields:
                    if selected & {"a", "b"}:
                        self.compare_combined(eval_field, reference_field, comparisons, llm)
                else:
                    for code in selected:
                        self.compare_subfield(eval_field, reference_field, code, comparisons, llm)

            else:
                for code in sub_fields:
                    self.compare_subfield(eval_field, reference_field, code, comparisons, llm)

    def compare_subfield(self, eval_field, reference_field, code, comparisons, llm=None) -> None:

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
            "score": self.compare_strings(eval_text, reference_text, llm)
        })

    def compare_combined(self, eval_field, reference_field, comparisons, llm=None) -> None:

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
            "score": self.compare_strings(eval_text, reference_text, llm)
        })

    @abstractmethod
    def compare_strings(self, eval_text: str, reference_text: str, llm=None) -> float:
        pass

    @staticmethod
    def get_field(record, tag: str) -> dict | None:
        return next((field for field in record.fields if field["tag"] == tag), None)

    @staticmethod
    def get_subfield(field: dict, code: str) -> str | None:

        if code in {"ind1", "ind2"}:
            return field.get(code)
        return next((subfield["value"] for subfield in field["subfields"] if subfield["code"] == code), None)

    @staticmethod
    def build_field_scores(comparisons: list[dict]) -> dict:

        checks = {}

        for comparison in comparisons:
            tag = comparison["eval_field"]
            score = comparison["score"]
            subfield = "/".join(comparison["sub_fields"])

            field = checks.setdefault(tag, {"score": []})
            field["score"].append(score)
            field.setdefault(subfield, []).append(score)

        for group in FIELD_GROUPS:
            tags = sorted(group)
            group_name = "/".join(tags)

            group_checks = {}

            for tag in tags:
                for key, scores in checks.get(tag, {}).items():
                    group_checks.setdefault(key, []).extend(scores)

            if group_checks:
                checks[group_name] = group_checks

        return {
            tag: {key: sum(scores) / len(scores) for key, scores in values.items()}
            for tag, values in checks.items()
        }