from .base import BaseMethod
from ..funcs import normalize_text

class TextMatchMethod(BaseMethod):

    name = "text-match"
    requires_text = True

    def run_doc(self, doc, llm=None):

        terms = [
            [doc.eval.isbn],
            [doc.eval.title_clean],
            [doc.eval.sub_title_clean],
            [doc.eval.parallel_title_clean],
            *doc.eval.people_name_variants,
            *doc.eval.company_names,
            doc.eval.locations_confident,
            doc.eval.publishers,
            doc.eval.years_confident
        ]

        unmatched = []
        total = 0
        matched_count = 0

        for term_list in terms:
            term_list = [t for t in term_list if t is not None]
            if not term_list:
                continue

            total += 1
            normalized = [normalize_text(t) for t in term_list]

            matched = [term in doc.text_normalized for term in normalized]

            if any(matched):
                matched_count += 1
            else:
                unmatched.append(term_list)

        score = matched_count / total if total else 1.0

        return {
            "score": score,
            "info": {
                "unmatched": unmatched
            }
        }