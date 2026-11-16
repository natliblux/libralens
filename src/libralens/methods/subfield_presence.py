from ..constants import FIELD_GROUPS
from .base import BaseMethod
from .subfield_cardinality import SubfieldCardinalityMethod

class SubfieldPresenceMethod(BaseMethod):

    name = "subfield-presence"
    requires_reference = True
    supported_fields = SubfieldCardinalityMethod.supported_fields
    
    def run_doc(self, doc, fields, llm=None):

        scores = []
        info = {}
        references = {}

        sources = [(doc.gold, "gold"), (doc.platinum, "platinum")]

        for reference, name in sources:
            if reference is None:
                continue

            result = self.compare_records(doc.eval, reference, fields)

            scores.append(result["score"])
            references[name] = {
                "score": result["score"],
                **result["fields"]
            }
            info[name] = result["comparisons"]

        return {
            "score": sum(scores) / len(scores) if scores else None,
            "references": references,
            "info": info
        }

    def compare_records(self, eval_record, reference_record, fields) -> dict:

        comparisons = []
        checks = {}

        for tag, subfields in fields.items():
            for code in subfields:
                eval_present = self.has_subfield(eval_record, {tag}, code)
                reference_present = self.has_subfield(reference_record, {tag}, code)

                comparisons.append({
                    "field": tag,
                    "subfield": code,
                    "eval_present": eval_present,
                    "reference_present": reference_present,
                    "score": float(not reference_present or eval_present)
                })

        for group in FIELD_GROUPS:
            tags = sorted(group)
            selected = set().union(*(fields.get(tag, set()) for tag in tags))

            if not selected:
                continue

            comparisons = [c for c in comparisons if c["field"] not in group]

            for code in selected:
                eval_present = self.has_subfield(eval_record, group, code)
                reference_present = self.has_subfield(reference_record, group, code)

                comparisons.append({
                    "field": "/".join(tags),
                    "subfield": code,
                    "eval_present": eval_present,
                    "reference_present": reference_present,
                    "score": float(not reference_present or eval_present)
                })

        for comparison in comparisons:
            field = checks.setdefault(comparison["field"], {"score": []})
            field["score"].append(comparison["score"])
            field[comparison["subfield"]] = comparison["score"]

        field_scores = {
            tag: {key: sum(values) / len(values) if isinstance(values, list) else values for key, values in checks.items()}
            for tag, checks in checks.items()
        }

        scores = [comparison["score"] for comparison in comparisons]

        return {
            "score": sum(scores) / len(scores) if scores else None,
            "fields": field_scores,
            "comparisons": comparisons
        }

    @staticmethod
    def has_subfield(record, tags: set[str], code: str) -> bool:
        return any(
            field["tag"] in tags and any(subfield["code"] == code for subfield in field["subfields"])
            for field in record.fields
        )