from .base import BaseMethod
from ..constants import TITLE_SEMANTICS_SYSTEM_PROMPT, TITLE_SEMANTICS_USER_PROMPT

class RecordUsabilityMethod(BaseMethod):

    name = "record-usability"

    supported_fields = {
        "020": ("a",),
        "110": ("a", "b"),
        "245": ("a",),
        "710": ("a", "b"),
    }

    requires_gold_or_platinum = True
    requires_llm = True

    def run_doc(self, doc, fields, llm=None):

        passed = []
        failed = []

        reference = doc.gold if doc.gold is not None else doc.platinum

        if "020" in fields and "a" in fields["020"]:
            self.check_isbn(doc.eval, reference, passed, failed)

        if "245" in fields and "a" in fields["245"]:
            self.check_title_presence(doc.eval, reference, passed, failed)
            self.check_title_semantics(doc.eval, reference, llm, passed, failed)

        company_tags = {tag for tag in {"110", "710"} & fields.keys() if fields[tag] & {"a", "b"}}
        if company_tags:
            self.check_company_names(doc.eval, reference, company_tags, passed, failed)

        return {
            "score": 1.0 if not failed else 0.0,
            "info": {
                "passed": passed,
                "failed": failed
            }
        }

    def check_title_presence(self, record, reference, passed, failed) -> None:

        result = {
            "criterion": "title-present",
            "eval": record.title,
            "reference": reference.title
        }

        if record.title is None:
            failed.append(result)
        else:
            passed.append(result)

    def check_title_semantics(self, record, reference, llm, passed, failed) -> None:

        result = {
            "criterion": "title-semantics",
            "eval": record.title,
            "reference": reference.title,
            "missing": []
        }

        if reference.title is None:
            passed.append(result)
            return

        if record.title is None:
            result["missing"] = [reference.title]
            failed.append(result)
            return

        llm_result = self.check_title_semantics_llm(
            eval_title=record.title,
            reference_title=reference.title,
            llm=llm
        )

        result["missing"] = llm_result["missing"]

        if llm_result["passed"]:
            passed.append(result)
        else:
            failed.append(result)

    def check_isbn(self, record, reference, passed, failed) -> None:

        result = {
            "criterion": "isbn-match",
            "eval": record.isbn,
            "reference": reference.isbn
        }

        if reference.isbn is None:
            passed.append(result)
        elif record.isbn == reference.isbn:
            passed.append(result)
        else:
            failed.append(result)

    def check_company_names(self, record, reference, tags, passed, failed) -> None:

        eval_names = [name for tag in tags for name in record.company_names[tag]]
        reference_names = [name for tag in tags for name in reference.company_names[tag]]

        result = {
            "criterion": "company-present",
            "eval": eval_names,
            "reference": reference_names
        }

        if not reference_names:
            passed.append(result)
        elif eval_names:
            passed.append(result)
        else:
            failed.append(result)

    def check_title_semantics(self, record, reference, llm, passed, failed) -> None:

        result = {
            "criterion": "title-semantics",
            "eval": record.title,
            "reference": reference.title,
            "missing": []
        }

        if reference.title is None:
            passed.append(result)
            return

        if record.title is None:
            result["missing"] = [reference.title]
            failed.append(result)
            return

        user_prompt = TITLE_SEMANTICS_USER_PROMPT.replace("[TITLE_1]", reference.title).replace("[TITLE_2]", record.title)
        response = llm.run(system_prompt=TITLE_SEMANTICS_SYSTEM_PROMPT, user_prompt=user_prompt).strip()

        if response.upper() != "OK":
            result["missing"] = [item.strip() for item in response.split(",") if item.strip()]

        if result["missing"]:
            failed.append(result)
        else:
            passed.append(result)