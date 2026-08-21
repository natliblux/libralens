from .base import BaseMethod

class EditDistanceMethod(BaseMethod):

    name = "edit-distance"
    requires_gold_or_platinum = True

    def run_doc(self, doc, llm=None):

        return {
            "score": 1.0,
            "info": {}
        }