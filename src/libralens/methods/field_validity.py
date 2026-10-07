import re
from datetime import datetime
from ..constants import GROUPED_FIELDS, MARC_LANGUAGE_CODES, MARC_RELATOR_CODES
from .base import BaseMethod

class FieldValidityMethod(BaseMethod):

    name = "field-validity"

    supported_fields = {
        "008": (),
        "020": ("a",),
        "041": ("a",),
        "100": ("4",),
        "110": ("4",),
        "700": ("4",),
        "710": ("4",)
    }

    def run_doc(self, doc, fields, llm=None):

        valid = []
        invalid = []

        if "008" in fields:
            self.check_008(doc.eval, valid, invalid)

        if "020" in fields and "a" in fields["020"]:
            self.check_isbn(doc.eval, valid, invalid)

        if "041" in fields and "a" in fields["041"]:
            self.check_041(doc.eval, valid, invalid)

        relator_tags = {tag for tag in GROUPED_FIELDS & fields.keys() if "4" in fields[tag]}
        if relator_tags:
            self.check_relators(doc.eval, relator_tags, valid, invalid)

        total = len(valid) + len(invalid)
        score = len(valid) / total if total else None

        return {
            "score": score,
            "info": {
                "valid": valid,
                "invalid": invalid
            }
        }

    def check_isbn(self, record, valid, invalid) -> None:

        if record.isbn_normalized is None:
            return

        result = {
            "field": "020",
            "part": "$a",
            "value": record.isbn_normalized,
        }

        if self.is_valid_isbn(record.isbn_normalized):
            valid.append(result)
        else:
            invalid.append(result)

    def check_041(self, record, valid, invalid) -> None:

        for lang_code in record.lang_codes:

            result = {
                "field": "041",
                "part": "$a",
                "value": lang_code,
            }

            if lang_code in MARC_LANGUAGE_CODES:
                valid.append(result)
            else:
                invalid.append(result)

    def check_008(self, record, valid, invalid) -> None:

        if record.zero_zero_eight is None:
            return

        if len(record.zero_zero_eight) < 38:
            invalid.append({
                "field": "008",
                "part": "length",
                "value": record.zero_zero_eight,
                "reason": f"expected at least 38 characters, found {len(record.zero_zero_eight)}",
            })
            return

        date = record.zero_zero_eight[0:6]

        date_result = {
            "field": "008",
            "part": "00-05",
            "value": date,
        }

        if self.is_valid_008_date(date):
            valid.append(date_result)
        else:
            invalid.append(date_result)

        language = record.zero_zero_eight[35:38]

        language_result = {
            "field": "008",
            "part": "35-37",
            "value": language,
        }

        if language in MARC_LANGUAGE_CODES:
            valid.append(language_result)
        else:
            invalid.append(language_result)

    def check_relators(self, record, tags, valid, invalid) -> None:

        for tag in tags:

            for relator in record.relators[tag]:

                result = {
                    "field": tag,
                    "part": "$4",
                    "value": relator,
                }

                if relator in MARC_RELATOR_CODES:
                    valid.append(result)
                else:
                    invalid.append(result)

    @staticmethod
    def is_valid_isbn(full_isbn: str) -> bool:

        isbn = re.sub(r"[\s-]", "", full_isbn)

        if len(isbn) == 10:
            return FieldValidityMethod.is_valid_isbn10(isbn)

        if len(isbn) == 13:
            return FieldValidityMethod.is_valid_isbn13(isbn)

        return False

    @staticmethod
    def is_valid_isbn10(isbn: str) -> bool:

        if not isbn[:9].isdigit():
            return False

        if not (isbn[-1].isdigit() or isbn[-1] in {"X", "x"}):
            return False

        total = 0

        for i, char in enumerate(isbn):
            value = 10 if char in {"X", "x"} else int(char)
            total += (10 - i) * value

        return total % 11 == 0

    @staticmethod
    def is_valid_isbn13(isbn: str) -> bool:

        if not isbn.isdigit():
            return False

        if not isbn.startswith(("978", "979")):
            return False

        total = sum(int(isbn[i]) * (1 if i % 2 == 0 else 3) for i in range(12))
        expected = (10 - total % 10) % 10

        return int(isbn[-1]) == expected

    @staticmethod
    def is_valid_008_date(value: str) -> bool:

        if not re.fullmatch(r"\d{6}", value):
            return False
        try:
            datetime.strptime(value, "%y%m%d")
            return True
        except ValueError:
            return False