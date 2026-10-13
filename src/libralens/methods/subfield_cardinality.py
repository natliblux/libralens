from .base import BaseMethod
from ..constants import MAPPED_FIELDS, MAPPING_GROUPS

class SubfieldCardinality(BaseMethod):

    name = "subfield-cardinality"

    supported_fields = {
        "008": (),
        "020": ("a",),
        "041": ("a",),
        "100": ("a", "b", "d", "0", "e", "4"),
        "110": ("a", "b", "d", "0", "e", "4"),
        "245": ("a", "b", "c", "d"),
        "264": ("a", "b", "c"),
        "300": ("a", "b"),
        "490": ("a",),
        "700": ("a", "b", "d", "0", "e", "4"),
        "710": ("a", "b", "d", "0", "e", "4"),
    }

    requires_gold_or_platinum = True

    def run_doc(self, doc, fields, llm=None):

        scores = []
        info = {}

        references = [
            (doc.gold, doc.gold_mapping, "gold"),
            (doc.platinum, doc.platinum_mapping, "platinum"),
        ]

        for reference, mapping, name in references:

            if reference is None:
                continue

            result = self.compare_records(doc.eval, reference, mapping, fields)

            if result["score"] is not None:
                scores.append(result["score"])

            info[name] = result

        return {
            "score": sum(scores) / len(scores) if scores else None,
            "info": info,
        }

    def compare_records(self, eval_record, reference_record, mapping, fields) -> dict:

        comparisons = []

        self.compare_standard_fields(eval_record, reference_record, fields, comparisons)
        self.compare_mapped_groups(eval_record, reference_record, mapping, fields, comparisons)

        scores = [comparison["score"] for comparison in comparisons]

        return {
            "score": sum(scores) / len(scores) if scores else None,
            "comparisons": comparisons,
        }

    def compare_standard_fields(self, eval_record, reference_record, fields, comparisons) -> None:

        for tag, sub_fields in fields.items():

            if tag in MAPPED_FIELDS:
                continue

            if tag == "008":

                eval_values = self.get_field_values(eval_record, tag)
                reference_values = self.get_field_values(reference_record, tag)

                comparison = self.create_comparison(eval_values, reference_values)

                comparisons.append({
                    "fields": [tag],
                    "subfield": None,
                    "score": comparison["score"],
                    "comparisons": [comparison],
                })

            else:

                for code in sub_fields:

                    eval_values = self.get_subfield_values(eval_record, {tag}, code)
                    reference_values = self.get_subfield_values(reference_record, {tag}, code)

                    comparison = self.create_comparison(eval_values, reference_values)

                    comparisons.append({
                        "fields": [tag],
                        "subfield": code,
                        "score": comparison["score"],
                        "comparisons": [comparison],
                    })

    def compare_mapped_groups(self, eval_record, reference_record, mapping, fields, comparisons) -> None:

        for tags in MAPPING_GROUPS:
            selected_subfields = set()
            for tag in tags:
                if tag in fields:
                    selected_subfields.update(fields[tag])
            for code in selected_subfields:
                comparisons.append(self.compare_mapped_subfield(eval_record, reference_record, mapping, tags, code))

    def compare_mapped_subfield(self, eval_record, reference_record, mapping, tags, code) -> dict:

        eval_fields = [field for field in eval_record.fields if field["tag"] in tags]
        reference_fields = [field for field in reference_record.fields if field["tag"] in tags]

        eval_by_id = {field["id"]: field for field in eval_fields}
        reference_by_id = {field["id"]: field for field in reference_fields}

        comparisons = []
        mapped_eval_ids = set()
        mapped_reference_ids = set()

        for eval_id, reference_id in mapping.items():

            if eval_id not in eval_by_id or reference_id not in reference_by_id:
                continue

            eval_field = eval_by_id[eval_id]
            reference_field = reference_by_id[reference_id]

            mapped_eval_ids.add(eval_id)
            mapped_reference_ids.add(reference_id)

            eval_values = self.get_subfield_values_in_field(eval_field, code)
            reference_values = self.get_subfield_values_in_field(reference_field, code)

            comparisons.append(self.create_comparison(eval_values, reference_values))

        for eval_field in eval_fields:

            if eval_field["id"] in mapped_eval_ids:
                continue

            eval_values = self.get_subfield_values_in_field(eval_field, code)

            if eval_values:
                comparisons.append(self.create_comparison(eval_values, []))

        for reference_field in reference_fields:

            if reference_field["id"] in mapped_reference_ids:
                continue

            reference_values = self.get_subfield_values_in_field(reference_field, code)

            if reference_values:
                comparisons.append(self.create_comparison([], reference_values))

        if not comparisons:
            comparisons.append(self.create_comparison([], []))

        scores = [comparison["score"] for comparison in comparisons]

        return {
            "fields": sorted(tags),
            "subfield": code,
            "score": sum(scores) / len(scores),
            "comparisons": comparisons,
        }

    def create_comparison(self, eval_values, reference_values) -> dict:

        eval_count = len(eval_values)
        reference_count = len(reference_values)

        return {
            "eval_values": eval_values,
            "reference_values": reference_values,
            "eval_count": eval_count,
            "reference_count": reference_count,
            "score": self.cardinality_score(eval_count, reference_count),
        }

    @staticmethod
    def cardinality_score(eval_count, reference_count) -> float:

        if eval_count == reference_count:
            return 1.0

        return min(eval_count, reference_count) / max(eval_count, reference_count)

    @staticmethod
    def get_field_values(record, tag) -> list[str]:
        return [field["value"] for field in record.fields if field["tag"] == tag]

    @staticmethod
    def get_subfield_values(record, tags, code) -> list[str]:

        return [
            subfield["value"]
            for field in record.fields
            if field["tag"] in tags
            for subfield in field["subfields"]
            if subfield["code"] == code
        ]

    @staticmethod
    def get_subfield_values_in_field(field, code) -> list[str]:
        return [subfield["value"] for subfield in field["subfields"] if subfield["code"] == code]