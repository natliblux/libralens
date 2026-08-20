from .text_match import TextMatchMethod
from .edit_distance import EditDistanceMethod

METHOD_CLASSES = [
    TextMatchMethod,
	EditDistanceMethod
]

METHODS = {
    method.name: method
    for method in METHOD_CLASSES
}