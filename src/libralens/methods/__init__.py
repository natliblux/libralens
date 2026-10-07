from .field_validity import FieldValidityMethod
from .text_match import TextMatchMethod
from .common_substring import CommonSubstringMethod
from .edit_distance import EditDistanceMethod
from .f1_score import F1ScoreMethod
from .precision_score import PrecisionMethod
from .recall_score import RecallMethod
from .subfield_cardinality import SubfieldCardinality
from .record_usability import RecordUsabilityMethod

METHOD_CLASSES = [
    FieldValidityMethod,
    TextMatchMethod,
    CommonSubstringMethod,
    EditDistanceMethod,
    F1ScoreMethod,
    PrecisionMethod,
    RecallMethod,
    SubfieldCardinality,
    RecordUsabilityMethod
]

METHODS = {
    method.name: method
    for method in METHOD_CLASSES
}