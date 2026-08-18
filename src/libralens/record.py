import xml.etree.ElementTree as ET
import re
from libralens.constants import RELEVANT_FIELDS
from .funcs import remove_namespaces
from .enums import InputFormat

class Record:

    def __init__(self, data: str, input_format: InputFormat):

        self.data = data
        self.input_format = input_format
        self.fields = []

        if self.input_format == InputFormat.XML:
            self.parse_xml()
        elif self.input_format == InputFormat.TEXT:
            self.parse_text()

    def parse_text(self):

        for line in self.data.splitlines():
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
                self.fields.append({
                    "tag": tag,
                    "value": value,
                })

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

                    subfields.append({
                        "code": code,
                        "value": value,
                    })
                self.fields.append({
                    "tag": tag,
                    "ind1": ind1,
                    "ind2": ind2,
                    "subfields": subfields,
                })

    def parse_xml(self):

        root = ET.fromstring(self.data)
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