from .base import BaseMethod

class ExampleMethod(BaseMethod):

    name = "example"

    requires_gold = True
    requires_text = True
    requires_llm = True

    def run(self, data, fields, llm=None):

        pass