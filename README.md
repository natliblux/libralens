# LibraLens
<p align="left">
  <img src="assets/logo.png" alt="LibraLens logo" width="400">
</p>

LibraLens is a Python library providing methods for the evaluation of MARC 21 records. It supports records in xml and text format. Records can be evaluated independently or compared against corresponding **gold** and **platinum** standards:

* **Gold** represents a record based on experienced human-level cataloging.
* **Platinum** represents a maximized record version based on unlimited resources and exceeding general cataloging expectations.

LibraLens is designed as a toolbox, allowing different evaluation methods and MARC fields to be selected depending on the analysis to perform.

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
    eval="records/",
    methods=["method1", "method2"],
    fields=["100", "245", "264"],
    gold="gold/",
    platinum="platinum/",
    text="text/"
)

results = ll.run()
```

The parameters `fields`, `gold`, `platinum` and `text` are optional. If `fields` is ommited, all supported fields are considered by default.

### Command Line Interface

Use method1 to evaluate a .txt file (single record only) or an .xml file (single or multiple records):

```bash
libralens --eval record.txt --methods method1
```

Evaluate record(s) using multiple methods:

```bash
libralens --eval record.xml --methods method1 method2

```

Evaluate all records (within .xml/.txt files) within a directory:

```bash
libralens --eval records/ --methods method1
```

Limit the evaluation to specific MARC fields:

```bash
libralens --eval record.xml --methods method1 --fields 100 110 700 710
```

Provide corresponding gold standards and platinum standards:

```bash
libralens --eval records/ --methods method1 --gold gold/ --platinum platinum/
```

Certain methods require the corresponding document plain text:

```bash

libralens --eval records/ --methods method1 --text text/

```

The short forms `-e`, `-m`, `-f`, `-g`, `-p` and `-t` can be used instead of their corresponding long options. Check `--help` for more info.

## Document Matching

All data belonging to the same document is matched through its base filename. This includes the eval records, the corresponding gold and platinum standards, and plain text. For example, the following files are considered to belong to the same document:

```text
eval/
    record.xml
gold/
    record.xml
platinum/
    record.xml
text/
    record.txt
```

Gold and platinum files must have the same filename as the corresponding eval file. Plain text files use the same base filename but always use the `.txt` extension. When matched `.xml` files contain multiple records, eval, gold and platinum records are paired by their order within the file. The number of records must therefore match across the corresponding files. For a multi-record `.xml` file, the corresponding plain text is provided through a directory with the same base filename:

```text
eval/
    records.xml
gold/
    records.xml
platinum/
    records.xml
text/
    records/
        00.txt
        01.txt
        02.txt
```

The numbered text files correspond to the records by their order within the `.xml` file, starting at `0`. Leading zeros are optional and ignored when determining the record. The number of text files must match the number of records.

## LLM Configuration

Some evaluation methods require access to an LLM. LibraLens supports LLMs exposed through an OpenAI-compatible Chat Completions API. The connection can be configured through the following environment variables:

- `LIBRALENS_LLM_URL` - required
- `LIBRALENS_LLM_MODEL` - required
- `LIBRALENS_LLM_KEY` - optional, depending on the endpoint

For example:

```bash
export LIBRALENS_LLM_URL="https://api.openai.com/v1/v1"
export LIBRALENS_LLM_MODEL="gpt-5"
export LIBRALENS_LLM_KEY="..."
```

The API key can be omitted for endpoints that do not require authentication, such as some locally hosted models.

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