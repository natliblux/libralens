from pathlib import Path
import xml.etree.ElementTree as ET
from .record import Record
from .data import Data
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

def load_data(input_path: str | Path, gold_path: str | Path | None = None, platinum_path: str | Path | None = None) -> list[Data]:

    input_path = Path(input_path)
    gold_path = Path(gold_path) if gold_path is not None else None
    platinum_path = Path(platinum_path) if platinum_path is not None else None

    if input_path.is_file():
        return pair_files(input_path, gold_path, platinum_path)

    if input_path.is_dir():

        if gold_path is not None and not gold_path.is_dir():
            raise ValueError("when input is a directory, gold must also be a directory")

        if platinum_path is not None and not platinum_path.is_dir():
            raise ValueError("when input is a directory, platinum must also be a directory")

        data = []

        for input_file in sorted(input_path.iterdir()):
            if input_file.suffix.lower() not in {format.extension for format in InputFormat}:
                continue

            gold_file = None
            platinum_file = None

            if gold_path is not None:
                gold_file = gold_path / input_file.name
                if not gold_file.exists():
                    raise ValueError(f"no matching gold file found for: {input_file.name}")

            if platinum_path is not None:
                platinum_file = platinum_path / input_file.name
                if not platinum_file.exists():
                    raise ValueError(f"no matching platinum file found for: {input_file.name}")
                
            data.extend(pair_files(input_file, gold_file, platinum_file))

        return data
    raise ValueError(f"path does not exist: {input_path}")

def pair_files(input_file: Path, gold_file: Path | None = None, platinum_file: Path | None = None) -> list[Data]:

    records = load_file(input_file)
    gold_records = load_file(gold_file) if gold_file is not None else None
    platinum_records = load_file(platinum_file) if platinum_file is not None else None

    if gold_records is not None and len(records) != len(gold_records):
        raise ValueError(f"record count mismatch between {input_file.name} ({len(records)}) and gold ({len(gold_records)})")

    if platinum_records is not None and len(records) != len(platinum_records):
        raise ValueError(f"record count mismatch between {input_file.name} ({len(records)}) and platinum ({len(platinum_records)})")

    data = []

    for i, record in enumerate(records):

        gold = gold_records[i] if gold_records is not None else None
        platinum = platinum_records[i] if platinum_records is not None else None
        data.append(Data(record=record, gold=gold, platinum=platinum))

    return data