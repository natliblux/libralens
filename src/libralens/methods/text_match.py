from .base import BaseMethod
from ..funcs import normalize_text

class TextMatchMethod(BaseMethod):

    name = "text-match"
    requires_text = True

    def run_doc(self, doc, llm=None):

        terms = [
            [doc.eval.isbn],
            *doc.eval.people_name_variants,
            *doc.eval.company_names
        ]

        unmatched = []

        for term_list in terms:
            term_list = [t for t in term_list if t is not None]
            if not term_list:
                continue
            normalized = [normalize_text(t) for t in term_list]
            matched = [n in doc.text_normalized for n in normalized]
            if not any(matched):
                unmatched.append(term_list)

        return {"unmatched": unmatched}