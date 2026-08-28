import xml.etree.ElementTree as ET
import re
import unicodedata

def record_to_xml(record) -> str:

    root = ET.Element("record", xmlns="http://www.loc.gov/MARC21/slim")

    for field in record.fields:

        if "value" in field:
            element = ET.SubElement(
                root,
                "controlfield",
                tag=field["tag"]
            )
            element.text = field["value"]

        else:
            element = ET.SubElement(
                root,
                "datafield",
                tag=field["tag"],
                ind1=field["ind1"],
                ind2=field["ind2"]
            )

            for subfield in field["subfields"]:
                subfield_element = ET.SubElement(
                    element,
                    "subfield",
                    code=subfield["code"]
                )
                subfield_element.text = subfield["value"]

    ET.indent(root, space="    ")

    return ET.tostring(
        root,
        encoding="unicode",
        xml_declaration=False
    )

def join_subfields(field: dict, codes: set[str]) -> str:

    values = [
        subfield["value"]
        for subfield in field["subfields"]
        if subfield["code"] in codes
    ]

    return " ".join(values)

def remove_namespaces(root: ET.Element) -> ET.Element:

    for elem in root.iter():
        if "}" in elem.tag:
            elem.tag = elem.tag.split("}", 1)[1]

    return root

def normalize_text(text: str) -> str:

    text = unicodedata.normalize("NFKC", text)
    text = text.lower()
    text = re.sub(r"\s+", " ", text)
    return text.strip()

def remove_angle_brackets(s: str) -> str:
    if s is None:
        return None
    return s.replace("<<", "").replace(">>", "")