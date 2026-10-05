from .text_match import TextMatchMethod
from .edit_distance import EditDistanceMethod
from .common_substring import CommonSubstringMethod
from .field_validity import FieldValidityMethod
from .record_usability import RecordUsabilityMethod
from .f1_score import F1ScoreMethod
from .subfield_cardinality import SubfieldCardinality

METHOD_CLASSES = [
    TextMatchMethod,
    EditDistanceMethod,
    CommonSubstringMethod,
    FieldValidityMethod,
    RecordUsabilityMethod,
	F1ScoreMethod,
	SubfieldCardinality
]

METHODS = {
    method.name: method
    for method in METHOD_CLASSES
}