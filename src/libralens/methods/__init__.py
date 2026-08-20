from .example import ExampleMethod

METHOD_CLASSES = [
    ExampleMethod,
]

METHODS = {
    method.name: method
    for method in METHOD_CLASSES
}