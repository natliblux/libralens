# LibraLens
<p align="left">
  <img src="assets/logo.png" alt="LibraLens logo" width="400">
</p>

LibraLens is a Python library providing tools for the evaluation of MARC 21 records. It supports records in text and xml format. Records can be evaluated independently or compared against corresponding **gold** and **platinum** standards:

* **Gold** represents a record based on experienced human-level cataloging.
* **Platinum** represents a maximized record version based on unlimited resources and exceeding general cataloging expectations.

LibraLens is designed as a toolbox, allowing different evaluation tools and MARC fields to be selected depending on the analysis to perform.

## Installation

Install LibraLens from the project directory:

```bash
pip install .
```

## Usage

LibraLens can be used either directly as a Python library or through the provided command-line interface.

### Python Library

The `LibraLens` class provides the main entry point to the library:

```python
from libralens import LibraLens

ll = LibraLens(
    eval="records/eval/",
    gold="records/gold/",
    platinum="records/platinum/",
    tools=["tool1", "tool2"],
    fields=["100", "245", "264"],
)

results = ll.run()
```

The parameters `gold`, `platinum` and `fields` are optional. If the latter is ommited, all supported fields are considered by default.
### Command Line Interface

Evaluate all records within an .xml file or a single record within a .txt file:

```bash
libralens --eval record.txt --tools tool1
```

Evaluate record(s) using multiple tools:

```bash
libralens --eval record.xml --tools tool1 tool2

```

Evaluate all records within a directory:

```bash
libralens --eval records/ --tools tool1
```

Limit the evaluation to specific MARC fields:

```bash
libralens --eval record.xml --tools tool1 --fields 100 245 264
```

Provide corresponding gold standards and platinum standards:

```bash
libralens --eval records/ --gold gold/ --platinum platinum/ --tools tool1
```

The short forms `-e`, `-g`, `-p`, `-t` and `-f` can be used instead of their corresponding long options. Check `--help` for more info.

## Record Matching

When directories are used, gold and platinum files are matched with the eval files by filename. When matched .xml files contain multiple records, records are paired by their order within the file. The number of records must therefore match across the corresponding eval, gold and platinum files. Gold and platinum standards are optional and can be provided independently.

## Supported MARC Fields

LibraLens currently supports the following MARC 21 fields and subfields:

| Field | Relevant subfields            |
| ----- | ----------------------------- |
| `008` | Entire control field          |
| `020` | `$a`                          |
| `041` | `$a`                          |
| `100` | `$a` `$b` `$d` `$0` `$e` `$4` |
| `110` | `$a` `$b` `$d` `$0` `$e` `$4` |
| `245` | `$a` `$b` `$c` `$d`           |
| `264` | `$a` `$b` `$c`                |
| `300` | `$a` `$b`                     |
| `490` | `$a`                          |
| `700` | `$a` `$b` `$d` `$0` `$e` `$4` |
| `710` | `$a` `$b` `$d` `$0` `$e` `$4` |