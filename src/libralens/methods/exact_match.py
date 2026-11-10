from .value_comparison import ValueComparisonMethod
from ..record import Record

class ExactMatchMethod(ValueComparisonMethod):

    name = "exact-match"
    combine_names = False

    supported_fields = {
        "008": ("00-05", "35-37"),
        "020": ("ind1", "ind2", "a"),
        "041": ("ind1", "ind2"),
        "100": ("ind1", "ind2", "d", "0", "e", "4"),
        "110": ("ind1", "ind2", "d", "0", "e", "4"),
        "245": ("ind1", "ind2"),
        "264": ("ind1", "ind2", "c"),
        "300": ("ind1", "ind2", "a", "b"),
        "490": ("ind1", "ind2"),
        "700": ("ind1", "ind2", "d", "0", "e", "4"),
        "710": ("ind1", "ind2", "d", "0", "e", "4")
    }

    def compare_strings(self, eval_text: str, reference_text: str) -> float:
        return float(eval_text == reference_text)

    def compare_subfield(self, eval_field, reference_field, code, comparisons) -> None:

        if eval_field["tag"] != "020" or code != "a":
            return super().compare_subfield(eval_field, reference_field, code, comparisons)

        eval_text = self.get_subfield(eval_field, code)
        reference_text = self.get_subfield(reference_field, code)

        if eval_text is None or reference_text is None:
            return

        eval_variants = set(Record.get_isbn_variants(eval_text))
        reference_variants = set(Record.get_isbn_variants(reference_text))
        score = float(bool(eval_variants & reference_variants))

        comparisons.append({
            "eval_field": eval_field["tag"],
            "reference_field": reference_field["tag"],
            "sub_fields": [code],
            "eval_text": eval_text,
            "reference_text": reference_text,
            "score": score
        })