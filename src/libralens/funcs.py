import xml.etree.ElementTree as ET
import re
import unicodedata

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