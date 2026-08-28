from abc import ABC, abstractmethod

class BaseMethod(ABC):

    name: str

    requires_gold = False
    requires_platinum = False
    requires_gold_or_platinum = False
    requires_text = False
    requires_llm = False

    def run(self, docs, fields, llm=None):

        results = []

        for doc in docs:
            result = self.run_doc(doc, fields, llm)
            results.append(result)

        return results

    @abstractmethod
    def run_doc(self, doc, fields, llm=None):
        pass