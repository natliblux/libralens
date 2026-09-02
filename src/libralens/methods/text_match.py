from .base import BaseMethod
from ..funcs import normalize_text

class TextMatchMethod(BaseMethod):

    name = "text-match"
    supported_fields = {
        "020": ("a",),
        "100": ("a", "b"),
        "110": ("a", "b"),
        "245": ("a", "b", "d"),
        "264": ("a", "b", "c"),
        "700": ("a", "b"),
        "710": ("a", "b"),
    }
    requires_text = True

    def run_doc(self, doc, fields, llm=None):

        terms = []

        if "020" in fields and "a" in fields["020"]:
            terms.append(doc.eval.isbn_variants)

        if "245" in fields:
            if "a" in fields["245"]:
                terms.append([doc.eval.title_clean])
            if "b" in fields["245"]:
                terms.append([doc.eval.sub_title_clean])
            if "d" in fields["245"]:
                terms.append([doc.eval.parallel_title_clean])

        if "264" in fields:
            if "a" in fields["264"]:
                terms.append(doc.eval.locations_confident)
            if "b" in fields["264"]:
                terms.append(doc.eval.publishers)
            if "c" in fields["264"]:
                terms.append(doc.eval.years_confident)

        for tag in {"100", "700"} & fields.keys():
            if fields[tag] & {"a", "b"}:
                terms.extend(doc.eval.people_name_variants[tag])

        for tag in {"110", "710"} & fields.keys():
            if fields[tag] & {"a", "b"}:
                terms.extend([[name] for name in doc.eval.company_names[tag]])

        matched_terms = []
        unmatched = []
        total = 0
        matched_count = 0

        for term_list in terms:
            term_list = [term for term in term_list if term is not None]

            if not term_list:
                continue

            total += 1

            normalized = [normalize_text(term) for term in term_list]
            matched = [term in doc.text_normalized for term in normalized]

            if any(matched):
                matched_count += 1
                matched_terms.append(term_list)
            else:
                unmatched.append(term_list)

        score = matched_count / total if total else None

        return {
            "score": score,
            "info": {
                "matched": matched_terms,
                "unmatched": unmatched
            }
        }