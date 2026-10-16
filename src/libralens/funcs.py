import xml.etree.ElementTree as ET
import re
import unicodedata
import fitz
from pathlib import Path
from pathlib import Path
import fitz
from .constants import PDF_N_PAGES, PDF_LARGE_IMG_DIM, PDF_IMAGE_SCALE

def compute_scores(results: list, methods: list) -> tuple:

    # per-document scores
    document_scores = {}

    for result in results:
        scores = [
            method_result["score"]
            for method_result in result["methods"].values()
            if method_result["score"] is not None
        ]

        document_score = sum(scores) / len(scores) if scores else None

        result["score"] = document_score
        document_scores[result["id"]] = document_score

    # per-method scores
    method_scores = {}

    for method in methods:
        scores = [
            result["methods"][method]["score"]
            for result in results
            if method in result["methods"] and result["methods"][method]["score"] is not None
        ]

        if scores:
            method_scores[method] = sum(scores) / len(scores)

    # overall score
    scores = [
        score
        for score in document_scores.values()
        if score is not None
    ]

    overall_score = sum(scores) / len(scores) if scores else None

    return document_scores, method_scores, overall_score

def extract_pdf_images(pdf_path: Path, output_dir: Path) -> None:

    with fitz.open(pdf_path) as pdf:
        n_pages = len(pdf)
        if n_pages == 0:
            raise ValueError(f"pdf contains zero pages: {pdf_path}")

        indices = sorted(set(range(min(PDF_N_PAGES, n_pages))) | set(range(max(0, n_pages - PDF_N_PAGES), n_pages)))

        for j, i in enumerate(indices):
            page = pdf[i]
            scale = min(PDF_IMAGE_SCALE, PDF_LARGE_IMG_DIM / max(page.rect.width, page.rect.height))
            pix = page.get_pixmap(matrix=fitz.Matrix(scale, scale), colorspace=fitz.csRGB, alpha=False)
            pix.save(output_dir / f"{j:02d}.png")

def extract_pdf_text(pdf_path: str | Path) -> str:

    with fitz.open(pdf_path) as doc:
        text = "\n\n".join(page.get_text("text") for page in doc)
    text = re.sub(r"(\w)-\n(\w)", r"\1\2", text)
    text = re.sub(r"(?<!\n)\n(?!\n)", " ", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n\s*\n", "\n\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"\n +", "\n", text)
    return text.strip()

def record_to_xml(record) -> str:

    root = ET.Element("record", xmlns="http://www.loc.gov/MARC21/slim")

    for field in record.fields:

        if "value" in field:
            element = ET.SubElement(root, "controlfield", tag=field["tag"])
            element.text = field["value"]
        else:
            element = ET.SubElement(root, "datafield", tag=field["tag"], ind1=field["ind1"], ind2=field["ind2"])
            for subfield in field["subfields"]:
                subfield_element = ET.SubElement(element, "subfield", code=subfield["code"])
                subfield_element.text = subfield["value"]

    ET.indent(root, space="    ")
    return ET.tostring(root, encoding="unicode", xml_declaration=False)

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