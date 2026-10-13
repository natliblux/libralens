from scipy.optimize import linear_sum_assignment
from Levenshtein import ratio
from .funcs import normalize_text, join_subfields
from .constants import FIELD_GROUPS, MAPPING_264_IND_WEIGHT, MAPPING_NAMES_IND_WEIGHT

def create_mapping(eval_record, reference_record) -> dict[int, int]:

    mapping = {}
    for tags in FIELD_GROUPS:
        mapping.update(map_field_group(eval_record, reference_record, tags, {"a", "b"}, MAPPING_NAMES_IND_WEIGHT))
    mapping.update(map_field_group(eval_record, reference_record, {"264"}, {"a", "b", "c"}, MAPPING_264_IND_WEIGHT))

    return mapping

def map_field_group(eval_record, reference_record, tags: set[str], subfields: set[str], indicator_weight: float) -> dict[int, int]:

    eval_fields = [field for field in eval_record.fields if field["tag"] in tags]
    reference_fields = [field for field in reference_record.fields if field["tag"] in tags]

    if not eval_fields or not reference_fields:
        return {}

    similarities = [
        [field_similarity(eval_field, reference_field, subfields, indicator_weight) for reference_field in reference_fields]
        for eval_field in eval_fields
    ]

    rows, cols = linear_sum_assignment(similarities, maximize=True)

    return {eval_fields[row]["id"]: reference_fields[col]["id"] for row, col in zip(rows, cols)}

def field_similarity(field_1: dict, field_2: dict, subfields: set[str], indicator_weight: float) -> float:

    value_1 = join_subfields(field_1, subfields)
    value_2 = join_subfields(field_2, subfields)

    content_similarity = ratio(normalize_text(value_1), normalize_text(value_2))

    if indicator_weight == 0:
        return content_similarity

    indicator_similarity = ((field_1["ind1"] == field_2["ind1"]) + (field_1["ind2"] == field_2["ind2"])) / 2

    return (1 - indicator_weight) * content_similarity + indicator_weight * indicator_similarity