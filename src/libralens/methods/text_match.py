from .base import BaseMethod
from ..funcs import normalize_text

class TextMatchMethod(BaseMethod):

    name = "text-match"
    supported_fields = {
        "020": ("a"),
        "094": ("a"),
        "100": ("a", "b"),
        "110": ("a", "b"),
        "245": ("a", "b", "d"),
        "264": ("a", "b", "c"),
        "700": ("a", "b"),
        "710": ("a", "b")
    }
    requires_text = True

    def run_doc(self, doc, fields, llm=None):

        terms = []

        # isbn
        if "020" in fields and "a" in fields["020"]:
            terms.append({
                "field": "020",
                "subfields": ["a"],
                "value": doc.eval.isbn_raw,
                "variants": doc.eval.isbn_variants,
            })

        # 094
        if "094" in fields and "a" in fields["094"]:
            terms.append({
                "field": "094",
                "subfields": ["a"],
                "value": doc.eval.zero_ninety_four,
                "variants": [doc.eval.zero_ninety_four_clean],
            })

        # title
        if "245" in fields:
            if "a" in fields["245"]:
                terms.append({
                    "field": "245",
                    "subfields": ["a"],
                    "value": doc.eval.title,
                    "variants": [doc.eval.title_clean],
                })

            if "b" in fields["245"]:
                terms.append({
                    "field": "245",
                    "subfields": ["b"],
                    "value": doc.eval.sub_title,
                    "variants": [doc.eval.sub_title_clean],
                })

            if "d" in fields["245"]:
                terms.append({
                    "field": "245",
                    "subfields": ["d"],
                    "value": doc.eval.parallel_title,
                    "variants": [doc.eval.parallel_title_clean],
                })

        # publication
        if "264" in fields:
            if "a" in fields["264"]:
                for location in doc.eval.locations_confident:
                    terms.append({
                        "field": "264",
                        "subfields": ["a"],
                        "value": location,
                        "variants": [location],
                    })

            if "b" in fields["264"]:
                for publisher in doc.eval.publishers:
                    terms.append({
                        "field": "264",
                        "subfields": ["b"],
                        "value": publisher,
                        "variants": [publisher],
                    })

            if "c" in fields["264"]:
                for year in doc.eval.years_confident:
                    terms.append({
                        "field": "264",
                        "subfields": ["c"],
                        "value": year,
                        "variants": [year],
                    })

        # person names
        for tag in {"100", "700"} & fields.keys():
            if fields[tag] & {"a", "b"}:
                for name, variants in zip(doc.eval.people_names[tag], doc.eval.people_name_variants[tag]):
                    terms.append({
                        "field": tag,
                        "subfields": sorted(fields[tag] & {"a", "b"}),
                        "value": name,
                        "variants": variants,
                    })

        # corporate names
        for tag in {"110", "710"} & fields.keys():
            if fields[tag] & {"a", "b"}:
                for name in doc.eval.company_names[tag]:
                    terms.append({
                        "field": tag,
                        "subfields": sorted(fields[tag] & {"a", "b"}),
                        "value": name,
                        "variants": [name],
                    })

        matched = []
        unmatched = []
        total = 0
        matched_count = 0

        for term in terms:

            variants = [variant for variant in term["variants"] if variant is not None]
            if not variants:
                continue

            total += 1

            matched_variant = next(
                (
                    variant
                    for variant in variants
                    if normalize_text(variant) in doc.text_normalized
                ),
                None,
            )

            result = {
                "field": term["field"],
                "subfields": term["subfields"],
                "value": term["value"],
            }

            if matched_variant is not None:
                matched_count += 1
                result["matched_variant"] = matched_variant
                matched.append(result)
            else:
                unmatched.append(result)

        score = matched_count / total if total else None

        return {
            "score": score,
            "info": {
                "matched": matched,
                "unmatched": unmatched,
            },
        }