from .field_validity import FieldValidityMethod
from .text_match import TextMatchMethod
from .entity_coverage import EntityCoverageMethod
from .semantic_recall import SemanticRecallMethod
from .common_substring import CommonSubstringMethod
from .edit_distance import EditDistanceMethod
from .exact_match import ExactMatchMethod
from .f1_score import F1ScoreMethod
from .precision_score import PrecisionMethod
from .recall_score import RecallMethod
from .subfield_cardinality import SubfieldCardinalityMethod
from .subfield_presence import SubfieldPresenceMethod
from .human_rating import HumanRatingMethod

METHOD_CLASSES = [
    FieldValidityMethod,
    TextMatchMethod,
    EntityCoverageMethod,
    SemanticRecallMethod,
    CommonSubstringMethod,
    EditDistanceMethod,
    ExactMatchMethod,
    F1ScoreMethod,
    PrecisionMethod,
    RecallMethod,
    SubfieldCardinalityMethod,
    SubfieldPresenceMethod,
    HumanRatingMethod
]

METHODS = {
    method.name: method
    for method in METHOD_CLASSES
}