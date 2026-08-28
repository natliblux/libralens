from .base import BaseMethod
from ..funcs import normalize_text, join_subfields

class TextMatchMethod(BaseMethod):

    name = "text-match"
    requires_text = True

    def run_doc(self, doc, fields, llm=None):

        terms = []

        if "020" in fields:
            terms.append([doc.eval.isbn])

        if "245" in fields:
            terms.extend([
                [doc.eval.title_clean],
                [doc.eval.sub_title_clean],
                [doc.eval.parallel_title_clean]
            ])

        person_tags = {"100", "700"} & set(fields)

        for field in doc.eval.fields:
            if field["tag"] not in person_tags:
                continue
            name = join_subfields(field, {"a", "b"})
            if name:
                terms.append(doc.eval.get_people_name_variants(name))

        company_tags = {"110", "710"} & set(fields)

        for field in doc.eval.fields:

            if field["tag"] not in company_tags:
                continue
            name = join_subfields(field, {"a", "b"})
            if name:
                terms.append([name])

        if "264" in fields:
            terms.extend([
                doc.eval.locations_confident,
                doc.eval.publishers,
                doc.eval.years_confident
            ])

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

        score = (matched_count / total if total else 1.0)

        return {
            "score": score,
            "info": {
                "matched": matched_terms,
                "unmatched": unmatched
            }
        }