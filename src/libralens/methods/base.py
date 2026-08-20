from abc import ABC, abstractmethod

class BaseMethod(ABC):

    name: str

    requires_gold = False
    requires_platinum = False
    requires_text = False
    requires_llm = False

    @abstractmethod
    def run(self, data, fields, llm=None):
        pass