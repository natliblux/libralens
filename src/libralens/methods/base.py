from abc import ABC, abstractmethod
from tqdm import tqdm

class BaseMethod(ABC):

    name: str

    requires_gold = False
    requires_platinum = False
    requires_gold_or_platinum = False
    requires_text = False
    requires_llm = False

    def run(self, docs, fields, llm=None, verbose=False, desc=None):

        results = []

        iterator = tqdm(docs, desc=desc or self.name) if verbose else docs
        for doc in iterator:
            results.append(self.run_doc(doc=doc, fields=fields, llm=llm))

        return results

    @abstractmethod
    def run_doc(self, doc, fields, llm=None):
        pass