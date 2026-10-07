import xml.etree.ElementTree as ET
import re
from libralens.constants import RELEVANT_FIELDS
from .funcs import remove_namespaces, remove_angle_brackets, join_subfields
from .enums import InputFormat
from itertools import permutations

class Record:

    def __init__(self, data: str, input_format: InputFormat):

        self.fields = []

        if input_format == InputFormat.XML:
            self.parse_xml(data=data)
        elif input_format == InputFormat.TEXT:
            self.parse_text(data=data)

        for i, field in enumerate(self.fields):
            field["id"] = i

        self.parse_fields()

    def parse_fields(self) -> None:

        self.zero_zero_eight = None
        self.title = None
        self.sub_title = None
        self.contributors = None
        self.parallel_title = None
        self.four_nine_zero = None
        self.isbn_raw = None
        self.isbn_normalized = None
        self.isbn_variants = []
        self.lang_codes = []
        self.locations = []
        self.publishers = []
        self.years = []
        self.people_names = {
            "100": [],
            "700": [],
        }
        self.company_names = {
            "110": [],
            "710": [],
        }
        self.relators = {
            "100": [],
            "110": [],
            "700": [],
            "710": [],
        }
        self.authorities = {
            "100": [],
            "110": [],
            "700": [],
            "710": [],
        }

        for field in self.fields:
            tag = field["tag"]
            if tag == "008":
                self.zero_zero_eight = field["value"]
            elif tag == "020":
                self.isbn_raw = next((s["value"] for s in field["subfields"] if s["code"] == "a"), None)
                self.isbn_normalized = self.normalize_isbn(self.isbn_raw)
                self.isbn_variants = self.get_isbn_variants(self.isbn_raw)
            elif tag == "041":
                self.lang_codes = [s["value"] for s in field["subfields"] if s["code"] == "a"]
            elif tag == "245":
                self.title = next((s["value"] for s in field["subfields"] if s["code"] == "a"), None)
                self.sub_title = next((s["value"] for s in field["subfields"] if s["code"] == "b"), None)
                self.contributors = next((s["value"] for s in field["subfields"] if s["code"] == "c"), None)
                self.parallel_title = next((s["value"] for s in field["subfields"] if s["code"] == "d"), None)
            elif tag == "264":
                location = next((s["value"] for s in field["subfields"] if s["code"] == "a"), None)
                if location:
                    self.locations.append(location)
                publisher = next((s["value"] for s in field["subfields"] if s["code"] == "b"), None)
                if publisher:
                    self.publishers.append(publisher)
                year = next((s["value"] for s in field["subfields"] if s["code"] == "c"), None)
                if year:
                    self.years.append(year)
            elif tag in {"100", "700"}:
                name = join_subfields(field, {"a", "b"})
                if name:
                    self.people_names[tag].append(name)
                relator = next((s["value"] for s in field["subfields"] if s["code"] == "4"), None)
                if relator:
                    self.relators[tag].append(relator)

                authority = next((s["value"] for s in field["subfields"] if s["code"] == "0"), None)
                if authority:
                    self.authorities[tag].append(authority)
            elif tag in {"110", "710"}:
                name = join_subfields(field, {"a", "b"})
                if name:
                    self.company_names[tag].append(name)
                relator = next((s["value"] for s in field["subfields"] if s["code"] == "4"), None)
                if relator:
                    self.relators[tag].append(relator)
                authority = next((s["value"] for s in field["subfields"] if s["code"] == "0"), None)
                if authority:
                    self.authorities[tag].append(authority)
            elif tag == "490":
                self.four_nine_zero = next((s["value"] for s in field["subfields"] if s["code"] == "a"), None)

        self.four_nine_zero_clean = remove_angle_brackets(self.four_nine_zero)
        self.title_clean = remove_angle_brackets(self.title)
        self.sub_title_clean = remove_angle_brackets(self.sub_title)
        self.parallel_title_clean = remove_angle_brackets(self.parallel_title)
        self.locations_confident = [l for l in self.locations if not l.endswith("]")]
        self.years_confident = [y for y in self.years if not y.endswith("]") and not y.endswith("?")]
        self.people_name_variants = {tag: [self.get_people_name_variants(name) for name in names] for tag, names in self.people_names.items()}

    def get_isbn_variants(self, isbn: str | None) -> list[str]:

        if isbn is None:
            return []
        compact = isbn.replace("-", "").replace(" ", "")
        return list(dict.fromkeys([isbn, compact, isbn.replace("-", " ")]))

    def get_people_name_variants(self, name: str) -> list[str]:

        terms = [
            term.strip()
            for term in name.replace(",", " ").split()
            if term.strip()
        ]

        variants = []

        for ordering in permutations(terms):
            variants.append(" ".join(ordering))
            variants.append(", ".join(ordering))

        return list(dict.fromkeys(variants))

    def parse_text(self, data: str) -> None:

        for line in data.splitlines():
            if not line:
                continue

            # Find first digit and remove everything before it
            index = next((i for i, c in enumerate(line) if c.isdigit()), -1)

            if index == -1:
                continue

            line = line[index:]
            tag = line[:3]

            if tag not in RELEVANT_FIELDS:
                continue

            # MARC controlfields are 00X
            if tag.startswith("00"):
                value = line[4:].strip()
                self.fields.append({"tag": tag, "value": value})

            else:
                if len(line) < 6:
                    continue

                ind1 = line[4]
                ind2 = line[5]
                content = line[6:]
                relevant_subfields = RELEVANT_FIELDS[tag]
                content = self.repair_missing_subfield_dollars(content, relevant_subfields)
                pattern = r"(\$[A-Za-z0-9])([^$]+)"
                matches = re.findall(pattern, content)
                subfields = []

                for code, value in matches:
                    code = code[1:]
                    value = value.strip()

                    if relevant_subfields and code not in relevant_subfields:
                        continue

                    if value.endswith("##"):
                        value = value[:-2]

                    subfields.append({"code": code, "value": value})
                self.fields.append({
                    "tag": tag,
                    "ind1": ind1,
                    "ind2": ind2,
                    "subfields": subfields,
                })

    def parse_xml(self, data: str) -> None:

        root = ET.fromstring(data)
        root = remove_namespaces(root)

        for field in root:

            tag = field.attrib.get("tag")
            if tag not in RELEVANT_FIELDS:
                continue

            if field.tag == "controlfield":
                self.fields.append({
                    "tag": tag,
                    "value": (field.text or "").strip()
                })

            elif field.tag == "datafield":
                relevant_subfields = RELEVANT_FIELDS[tag]

                parsed_field = {
                    "tag": tag,
                    "ind1": field.attrib.get("ind1", " "),
                    "ind2": field.attrib.get("ind2", " "),
                    "subfields": [],
                }

                for subfield in field.findall("subfield"):
                    code = subfield.attrib["code"]

                    if relevant_subfields and code not in relevant_subfields:
                        continue

                    parsed_field["subfields"].append({
                        "code": code,
                        "value": (subfield.text or "").strip()
                    })

                self.fields.append(parsed_field)

    def repair_missing_subfield_dollars(self, content, allowed_subfields):

        if not allowed_subfields:
            return re.sub(r"##(?=[A-Za-z0-9])", "$", content)
        allowed = "".join(re.escape(s) for s in allowed_subfields)

        # Replace ##e, ##4, etc. by $e, $4, but only for allowed subfields
        return re.sub(rf"##(?=[{allowed}])", "$", content)

    def normalize_isbn(self, isbn: str | None) -> str | None:

        if isbn is None:
            return None

        return "".join(c for c in isbn if c.isdigit() or c in {"X", "x"})