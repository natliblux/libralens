from pathlib import Path
import xml.etree.ElementTree as ET
from .record import Record
from .data import Data
from .funcs import remove_namespaces
from .constants import SUPPORTED_EXTENSIONS

def load_records(path: str | Path) -> list[Record]:
    
    path = Path(path)

    if path.is_file():
        return load_file(path)

    if path.is_dir():
        records = []

        for file in sorted(path.iterdir()):
            if file.suffix.lower() in SUPPORTED_EXTENSIONS:
                records.extend(load_file(file))
        return records

    raise ValueError(f"Path does not exist: {path}")

def load_file(path: Path) -> list[Record]:

    suffix = path.suffix.lower()

    if suffix == ".xml":
        return load_xml_file(path)

    if suffix == ".txt":
        return load_text_file(path)

    raise ValueError(f"Unsupported file type: {path}")

def load_text_file(path: Path) -> list[Record]:

    data = path.read_text(encoding="utf-8")
    return [Record(data, "text")]

def load_xml_file(path: Path) -> list[Record]:

    data = path.read_text(encoding="utf-8")

    root = ET.fromstring(data)
    root = remove_namespaces(root)

    if root.tag == "record":
        return [Record(data, "xml")]

    records = []

    for element in root.findall(".//record"):
        record_xml = ET.tostring(element, encoding="unicode")
        records.append(Record(record_xml, "xml"))

    return records

def load_data(input_path: str | Path, gold_path: str | Path | None = None) -> list[Data]:

    input_path = Path(input_path)

    if gold_path is None:
        return [Data(record) for record in load_records(input_path)]

    gold_path = Path(gold_path)

    if input_path.is_file():
        return pair_files(input_path, gold_path)

    if input_path.is_dir():
        if not gold_path.is_dir():
            raise ValueError("When input is a directory, gold must also be a directory")

        data = []

        for input_file in sorted(input_path.iterdir()):
            if input_file.suffix.lower() not in SUPPORTED_EXTENSIONS:
                continue

            gold_file = gold_path / input_file.name

            if not gold_file.exists():
                raise ValueError(f"No matching gold file found for: {input_file.name}")

            data.extend(pair_files(input_file, gold_file))

        return data

    raise ValueError(f"Path does not exist: {input_path}")

def pair_files(input_file: Path, gold_file: Path) -> list[Data]:

    if not gold_file.is_file():
        raise ValueError(f"Gold file does not exist: {gold_file}")

    records = load_file(input_file)
    gold_records = load_file(gold_file)

    if len(records) != len(gold_records):
        raise ValueError(f"Record count mismatch between {input_file.name} ({len(records)}) and {gold_file.name} ({len(gold_records)})")

    return [Data(record, gold) for record, gold in zip(records, gold_records)]