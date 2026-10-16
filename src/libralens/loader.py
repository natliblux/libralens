from pathlib import Path
import re
import xml.etree.ElementTree as ET
import fitz
from .record import Record
from .document import Document
from .funcs import remove_namespaces
from .enums import InputFormat

def load_document_text(path: Path) -> str:

    if path.suffix.lower() == ".txt":
        return path.read_text(encoding="utf-8")

    if path.suffix.lower() == ".pdf":
        with fitz.open(path) as doc:
            text = "\n\n".join(page.get_text("text") for page in doc)
        text = re.sub(r"(\w)-\n(\w)", r"\1\2", text)
        text = re.sub(r"(?<!\n)\n(?!\n)", " ", text)
        text = re.sub(r"[ \t]+", " ", text)
        text = re.sub(r"\n\s*\n", "\n\n", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        text = re.sub(r"\n +", "\n", text)
        text = text.strip()
        return text

    raise ValueError(f"unsupported document text file type: {path}")

def load_records(path: str | Path) -> list[Record]:

    path = Path(path)

    if path.is_file():
        return load_file(path)

    if path.is_dir():
        records = []

        for file in sorted(path.iterdir()):
            if file.suffix.lower() in {format.extension for format in InputFormat}:
                records.extend(load_file(file))
        return records

    raise ValueError(f"Path does not exist: {path}")

def load_file(path: Path) -> list[Record]:

    suffix = path.suffix.lower()

    if suffix == InputFormat.XML.extension:
        return load_xml_file(path)
    if suffix == InputFormat.TEXT.extension:
        return load_text_file(path)

    raise ValueError(f"unsupported file type: {path}")

def load_text_file(path: Path) -> list[Record]:

    data = path.read_text(encoding="utf-8")
    return [Record(data, InputFormat.TEXT)]

def load_xml_file(path: Path) -> list[Record]:

    data = path.read_text(encoding="utf-8")

    root = ET.fromstring(data)
    root = remove_namespaces(root)

    if root.tag == "record":
        return [Record(data, InputFormat.XML)]

    records = []

    for element in root.findall(".//record"):
        record_xml = ET.tostring(element, encoding="unicode")
        records.append(Record(record_xml, InputFormat.XML))

    return records

def load_documents(
    eval_path: str | Path,
    gold_path: str | Path | None = None,
    platinum_path: str | Path | None = None,
    text_path: str | Path | None = None,
    pdf_path: str | Path | None = None,
) -> list[Document]:

    eval_path = Path(eval_path)
    gold_path = Path(gold_path) if gold_path is not None else None
    platinum_path = Path(platinum_path) if platinum_path is not None else None
    text_path = Path(text_path) if text_path is not None else None
    pdf_path = Path(pdf_path) if pdf_path is not None else None

    if eval_path.is_file():

        if gold_path is not None and not gold_path.is_file():
            raise ValueError("when eval is a file, gold must also be a file")
        if platinum_path is not None and not platinum_path.is_file():
            raise ValueError("when eval is a file, platinum must also be a file")
        return pair_files(eval_path, gold_path, platinum_path, text_path, pdf_path)

    if eval_path.is_dir():

        if gold_path is not None and not gold_path.is_dir():
            raise ValueError("when eval is a directory, gold must also be a directory")
        if platinum_path is not None and not platinum_path.is_dir():
            raise ValueError("when eval is a directory, platinum must also be a directory")
        if text_path is not None and not text_path.is_dir():
            raise ValueError("when eval is a directory, text must also be a directory")
        if pdf_path is not None and not pdf_path.is_dir():
            raise ValueError("when eval is a directory, pdf must also be a directory")

        documents = []

        for eval_file in sorted(eval_path.iterdir()):
            if eval_file.suffix.lower() not in {format.extension for format in InputFormat}:
                continue

            gold_file = None
            platinum_file = None
            text_source = None
            pdf_source = None


            if gold_path is not None:
                gold_file = gold_path / eval_file.name
                if not gold_file.exists():
                    raise ValueError(f"no matching gold file found for: {eval_file.name}")
            if platinum_path is not None:
                platinum_file = platinum_path / eval_file.name
                if not platinum_file.exists():
                    raise ValueError(f"no matching platinum file found for: {eval_file.name}")
            if text_path is not None:
                text_source = get_matching_text_source(eval_file, text_path)
            if pdf_path is not None:
                pdf_source = get_matching_pdf_source(eval_file, pdf_path)

            documents.extend(pair_files(eval_file, gold_file, platinum_file, text_source, pdf_source))

        return documents
    raise ValueError(f"path does not exist: {eval_path}")

def pair_files(
    eval_file: Path,
    gold_file: Path | None = None,
    platinum_file: Path | None = None,
    text_source: Path | None = None,
    pdf_source: Path | None = None
) -> list[Document]:

    records = load_file(eval_file)
    gold_records = load_file(gold_file) if gold_file is not None else None
    platinum_records = load_file(platinum_file) if platinum_file is not None else None

    if gold_records is not None and len(records) != len(gold_records):
        raise ValueError(f"record count mismatch between {eval_file.name} ({len(records)}) and gold ({len(gold_records)})")

    if platinum_records is not None and len(records) != len(platinum_records):
        raise ValueError(f"record count mismatch between {eval_file.name} ({len(records)}) and platinum ({len(platinum_records)})")

    texts = load_texts(text_source, len(records)) if text_source is not None else None
    pdfs = load_pdfs(pdf_source, len(records)) if pdf_source is not None else None

    documents = []

    for i, record in enumerate(records):

        gold = gold_records[i] if gold_records is not None else None
        platinum = platinum_records[i] if platinum_records is not None else None
        text = texts[i] if texts is not None else None
        pdf = pdfs[i] if pdfs is not None else None
        documents.append(Document(eval=record, gold=gold, platinum=platinum, text=text, pdf=pdf))

    return documents

def get_matching_text_source(eval_file: Path, text_path: Path) -> Path:

    text_file = text_path / f"{eval_file.stem}.txt"
    pdf_file = text_path / f"{eval_file.stem}.pdf"
    text_dir = text_path / eval_file.stem

    matches = [path for path in [text_file, pdf_file, text_dir] if path.exists()]

    if len(matches) > 1:
        raise ValueError(f"multiple matching text sources found for: {eval_file.name}")

    if matches:
        return matches[0]

    raise ValueError(f"no matching text found for: {eval_file.name}")

def load_texts(text_source: Path, n_records: int) -> list[str]:

    if text_source.is_file():
        if n_records != 1:
            raise ValueError(f"{text_source.name} cannot be matched to {n_records} records")
        return [load_document_text(text_source)]

    if not text_source.is_dir():
        raise ValueError(f"text path does not exist: {text_source}")

    files = [file for file in text_source.iterdir() if file.suffix.lower() in {".txt", ".pdf"} and file.stem.isdigit()]
    indices = [int(file.stem) for file in files]

    if len(indices) != len(set(indices)):
        raise ValueError(f"duplicate text indices found in {text_source}")

    files = sorted(files, key=lambda file: int(file.stem))
    indices = [int(file.stem) for file in files]
    expected = list(range(len(files)))

    if indices != expected:
        raise ValueError(f"text files in {text_source} must be consecutively numbered starting at 0")

    if len(files) != n_records:
        raise ValueError(f"text count mismatch for {text_source.name}: {n_records} records, {len(files)} text files")

    return [load_document_text(file) for file in files]

def get_matching_pdf_source(eval_file: Path, pdf_path: Path) -> Path:

    pdf_file = pdf_path / f"{eval_file.stem}.pdf"
    pdf_dir = pdf_path / eval_file.stem
    matches = [path for path in [pdf_file, pdf_dir] if path.exists()]

    if len(matches) > 1:
        raise ValueError(f"multiple matching PDF sources found for: {eval_file.name}")
    if matches:
        return matches[0]

    raise ValueError(f"no matching PDF found for: {eval_file.name}")

def load_pdfs(pdf_source: Path, n_records: int) -> list[Path]:

    if pdf_source.is_file():
        if pdf_source.suffix.lower() != ".pdf":
            raise ValueError(f"not a PDF file: {pdf_source}")
        if n_records != 1:
            raise ValueError(f"{pdf_source.name} cannot be matched to {n_records} records")
        return [pdf_source]

    if not pdf_source.is_dir():
        raise ValueError(f"PDF path does not exist: {pdf_source}")

    files = [file for file in pdf_source.iterdir() if file.suffix.lower() == ".pdf" and file.stem.isdigit()]
    indices = [int(file.stem) for file in files]

    if len(indices) != len(set(indices)):
        raise ValueError(f"duplicate PDF indices found in {pdf_source}")

    files = sorted(files, key=lambda file: int(file.stem))
    indices = [int(file.stem) for file in files]

    if indices != list(range(len(files))):
        raise ValueError(f"PDF files in {pdf_source} must be consecutively numbered starting at 0")

    if len(files) != n_records:
        raise ValueError(f"PDF count mismatch for {pdf_source.name}: {n_records} records, {len(files)} PDF files")

    return files