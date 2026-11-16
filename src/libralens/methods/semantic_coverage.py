from .value_comparison import ValueComparisonMethod
from ..funcs import join_subfields
from ..constants import SEMANTIC_COVERAGE_SYSTEM_PROMPT, SEMANTIC_COVERAGE_USER_PROMPT

class SemanticCoverageMethod(ValueComparisonMethod):

    name = "semantic-coverage"
    requires_llm = True
    combine_subfields = True

    supported_fields = {
        "110": ("a", "b"),
        "245": ("a", "b", "d"),
        "264": ("b",),
        "490": ("a",),
        "710": ("a", "b")
    }

    def compare_strings(self, eval_text: str, reference_text: str, llm=None) -> float:
        return float(not self.get_missing(eval_text, reference_text, llm))

    @staticmethod
    def get_missing(eval_text: str, reference_text: str, llm) -> list[str]:

        user_prompt = SEMANTIC_COVERAGE_USER_PROMPT.replace("[REFERENCE]", reference_text).replace("[EVAL]", eval_text)
        response = llm.run(system_prompt=SEMANTIC_COVERAGE_SYSTEM_PROMPT, user_prompt=user_prompt).strip()

        if response.upper() == "OK":
            return []

        return [item.strip() for item in response.split(",") if item.strip()]

    def compare_subfield(self, eval_field, reference_field, code, comparisons, llm=None) -> None:

        eval_text = self.get_subfield(eval_field, code)
        reference_text = self.get_subfield(reference_field, code)

        if eval_text is None or reference_text is None:
            return

        missing = self.get_missing(eval_text, reference_text, llm)

        comparisons.append({
            "eval_field": eval_field["tag"],
            "reference_field": reference_field["tag"],
            "sub_fields": [code],
            "eval_text": eval_text,
            "reference_text": reference_text,
            "score": float(not missing),
            "missing": missing
        })

    def compare_combined(self, eval_field, reference_field, comparisons, llm=None) -> None:

        eval_text = join_subfields(eval_field, {"a", "b"})
        reference_text = join_subfields(reference_field, {"a", "b"})

        if not eval_text or not reference_text:
            return

        missing = self.get_missing(eval_text, reference_text, llm)

        comparisons.append({
            "eval_field": eval_field["tag"],
            "reference_field": reference_field["tag"],
            "sub_fields": ["a", "b"],
            "eval_text": eval_text,
            "reference_text": reference_text,
            "score": float(not missing),
            "missing": missing
        })