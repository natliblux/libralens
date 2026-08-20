from pathlib import Path
import xml.etree.ElementTree as ET

from .record import Record
from .document import Document
from .funcs import remove_namespaces
from .enums import InputFormat

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

def load_file(path: Path, fields: list[str] | None = None) -> list[Record]:

    suffix = path.suffix.lower()

    if suffix == InputFormat.XML.extension:
        return load_xml_file(path, fields)
    if suffix == InputFormat.TEXT.extension:
        return load_text_file(path, fields)

    raise ValueError(f"unsupported file type: {path}")

def load_text_file(path: Path, fields: list[str] | None = None,) -> list[Record]:

    data = path.read_text(encoding="utf-8")
    return [Record(data, InputFormat.TEXT, fields)]

def load_xml_file(path: Path, fields: list[str] | None = None,) -> list[Record]:

    data = path.read_text(encoding="utf-8")

    root = ET.fromstring(data)
    root = remove_namespaces(root)

    if root.tag == "record":
        return [Record(data, InputFormat.XML, fields)]

    records = []

    for element in root.findall(".//record"):
        record_xml = ET.tostring(element, encoding="unicode")
        records.append(Record(record_xml, InputFormat.XML, fields))

    return records

def load_documents(
    eval_path: str | Path,
    gold_path: str | Path | None = None,
    platinum_path: str | Path | None = None,
    text_path: str | Path | None = None,
    fields: list[str] | None = None
) -> list[Document]:

    eval_path = Path(eval_path)
    gold_path = Path(gold_path) if gold_path is not None else None
    platinum_path = Path(platinum_path) if platinum_path is not None else None
    text_path = Path(text_path) if text_path is not None else None

    if eval_path.is_file():
        return pair_files(eval_path, gold_path, platinum_path, text_path, fields)

    if eval_path.is_dir():

        if gold_path is not None and not gold_path.is_dir():
            raise ValueError("when eval is a directory, gold must also be a directory")
        if platinum_path is not None and not platinum_path.is_dir():
            raise ValueError("when eval is a directory, platinum must also be a directory")
        if text_path is not None and not text_path.is_dir():
            raise ValueError("when eval is a directory, text must also be a directory")

        documents = []

        for eval_file in sorted(eval_path.iterdir()):
            if eval_file.suffix.lower() not in {format.extension for format in InputFormat}:
                continue

            gold_file = None
            platinum_file = None
            text_source = None

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

            documents.extend(pair_files(eval_file, gold_file, platinum_file, text_source, fields))

        return documents
    raise ValueError(f"path does not exist: {eval_path}")

def pair_files(
    input_file: Path,
    gold_file: Path | None = None,
    platinum_file: Path | None = None,
    text_source: Path | None = None,
    fields: list[str] | None = None,
) -> list[Document]:

    records = load_file(input_file, fields)
    gold_records = load_file(gold_file, fields) if gold_file is not None else None
    platinum_records = load_file(platinum_file, fields) if platinum_file is not None else None

    if gold_records is not None and len(records) != len(gold_records):
        raise ValueError(f"record count mismatch between {input_file.name} ({len(records)}) and gold ({len(gold_records)})")

    if platinum_records is not None and len(records) != len(platinum_records):
        raise ValueError(f"record count mismatch between {input_file.name} ({len(records)}) and platinum ({len(platinum_records)})")

    texts = load_texts(text_source, len(records)) if text_source is not None else None

    documents = []

    for i, record in enumerate(records):

        gold = gold_records[i] if gold_records is not None else None
        platinum = platinum_records[i] if platinum_records is not None else None
        text = texts[i] if texts is not None else None
        documents.append(Document(eval=record, gold=gold, platinum=platinum, text=text))

    return documents

def get_matching_text_source(eval_file: Path, text_path: Path) -> Path:

    text_file = text_path / f"{eval_file.stem}.txt"
    text_dir = text_path / eval_file.stem

    if text_file.exists():
        return text_file

    if text_dir.exists() and text_dir.is_dir():
        return text_dir

    raise ValueError(f"no matching text found for: {eval_file.name}")

def load_texts(text_source: Path, n_records: int) -> list[str]:

    if text_source.is_file():
        if n_records != 1:
            raise ValueError(f"{text_source.name} cannot be matched to {n_records} records")
        return [text_source.read_text(encoding="utf-8")]

    if not text_source.is_dir():
        raise ValueError(f"text path does not exist: {text_source}")

    files = [file for file in text_source.glob("*.txt") if file.stem.isdigit()]
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

    return [file.read_text(encoding="utf-8") for file in files]