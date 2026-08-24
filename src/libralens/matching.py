from scipy.optimize import linear_sum_assignment
from Levenshtein import ratio
from .funcs import normalize_text, join_subfields

PERSON_TAGS = {"100", "700"}
COMPANY_TAGS = {"110", "710"}

def create_mapping(eval_record, reference_record) -> dict[int, int]:

    mapping = {}
    mapping.update(map_field_group(eval_record, reference_record, PERSON_TAGS))
    mapping.update(map_field_group(eval_record, reference_record, COMPANY_TAGS))
    return mapping

def map_field_group(eval_record, reference_record, tags: set[str]) -> dict[int, int]:

    eval_fields = [field for field in eval_record.fields if field["tag"] in tags]
    reference_fields = [field for field in reference_record.fields if field["tag"] in tags]

    if not eval_fields or not reference_fields:
        return {}

    similarities = [
        [
            field_similarity(eval_field, reference_field)
            for reference_field in reference_fields
        ]
        for eval_field in eval_fields
    ]

    rows, cols = linear_sum_assignment(similarities, maximize=True)

    return {
        eval_fields[row]["id"]: reference_fields[col]["id"]
        for row, col in zip(rows, cols)
    }

def field_similarity(field_1: dict, field_2: dict) -> float:

    value_1 = join_subfields(field_1, {"a", "b"})
    value_2 = join_subfields(field_2, {"a", "b"})

    return ratio(normalize_text(value_1), normalize_text(value_2))