# LibraLens
<p align="left">
  <img src="assets/logo.png" alt="LibraLens logo" width="400">
</p>

LibraLens is a Python library providing methods for the evaluation of MARC 21 records. It supports records in XML and text format. Records can be evaluated independently or compared against corresponding **gold** and **platinum** standards:

* **Gold** represents a record based on experienced human-level cataloging.
* **Platinum** represents a maximized record version based on unlimited resources and exceeding general cataloging expectations.

LibraLens is designed as a toolbox, allowing different evaluation methods and MARC fields to be selected depending on the analysis to perform.

## Contents

- [Installation](#installation)
- [Usage](#usage)
- [Results](#results)
- [Configuration](#configuration)
- [Reference](#reference)

## Installation

LibraLens requires Python 3.10 or later. Using a virtual environment is recommended. Create and activate it using:

```bash
python -m venv .venv
source .venv/bin/activate
```

Install LibraLens from the project directory:

```bash
pip install .
```

Required Python dependencies are installed automatically.

## Usage

LibraLens can be used either directly as a Python library or through the provided command-line interface.

### Python Library

The `LibraLens` class provides the main entry point to the library:

```python
from libralens import LibraLens

ll = LibraLens(
    eval="records/",
    methods=["text-match", "edit-distance"],
    fields=["100", "245", "264"],
    gold="gold/",
    platinum="platinum/",
    text="text/"
)

results = ll.run()
```

The parameters `fields`, `gold`, `platinum` and `text` are optional. If `fields` is omitted, all supported fields are considered by default.

### Command Line Interface

Evaluate a .txt file (single record only) or an .xml file (single or multiple records) using the method `text-match`:

```bash
libralens --eval record.txt --methods text-match
```

Evaluate record(s) using multiple methods:

```bash
libralens --eval record.xml --methods text-match edit-distance
```

Evaluate all records (within .xml/.txt files) within a directory:

```bash
libralens --eval records/ --methods text-match
```

Limit the evaluation to specific MARC fields:

```bash
libralens --eval record.xml --methods text-match --fields 100 110 700 710
```

Provide corresponding gold and platinum standards:

```bash
libralens --eval records/ --methods text-match --gold gold/ --platinum platinum/
```

Certain methods require the corresponding document's plain text:

```bash
libralens --eval records/ --methods text-match --text text/
```

The short forms `-e`, `-m`, `-f`, `-g`, `-p` and `-t` can be used instead of their corresponding long options. Check `--help` for more info.

## Results

LibraLens evaluates each document individually with each selected method. These individual scores are then aggregated at three levels:

- **Document score** - aggregated score across all evaluation methods for a document.
- **Method score** - aggregated score across all evaluated documents for a method.
- **Dataset score** - overall aggregated score across the complete evaluation.

Scores are normalized between `0.0` and `1.0`, where higher values indicate better results. In addition to numerical scores, methods can provide diagnostic information describing identified problems.

### Python Library

After running an evaluation, the `LibraLens` instance provides access to the following results:

```python
ll.run()

ll.document_scores  # aggregated score for each document
ll.method_scores    # aggregated score for each method
ll.score            # overall dataset score
ll.results          # detailed results for each document and method
```

For example:

```python
print(ll.score)
# 0.801

print(ll.method_scores)
# {
#     "text-match": 0.602,
#     "edit-distance": 1.0
# }

print(ll.document_scores)
# [0.8, 0.833, 0.786, 0.786]
```

`ll.results` contains the detailed results organized by document and method:

```python
[
    {
        "score": 0.8,
        "methods": {
            "text-match": {
                "score": 0.6,
                "info": {
                   ...
                }
            },
            "edit-distance": {
                "score": 1.0,
                "info": {
                    ...
                }
            }
        }
    }
]
```

The `info` content is method-specific and provides additional information about identified problems.

### Command Line Interface

When using the command-line interface, LibraLens prints a summary of the evaluation:

```text
document scores
  0.800 document 0
  0.833 document 1
  0.786 document 2
  0.786 document 3

method scores
  0.602 text-match
  1.000 edit-distance

dataset score
  0.801 overall
```

Detailed diagnostic information is available through the Python library.

## Configuration

### Document Matching

Corresponding eval, gold, platinum, and plain-text data is matched through base filenames. For a single-record file, the following files are considered to belong to the same document:

```
eval/
    record.xml
gold/
    record.xml
platinum/
    record.xml
text/
    record.txt
```

Gold and platinum files must have the same filename as the corresponding eval file. Plain text files use the same base filename but always use the `.txt` extension.

When matched `.xml` files contain multiple records, eval, gold and platinum records are paired by their order within the file. The number of records must therefore match across the corresponding files. For a multi-record `.xml` file, the corresponding plain text is provided through a directory with the same base filename:

```
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
The numbered text files correspond to the records by their order within the `.xml` file, starting at `0`. Leading zeros are optional and do not affect matching. The number of text files must match the number of records.

### LLM Configuration

Some evaluation methods require access to an LLM. LibraLens supports LLMs exposed through an OpenAI-compatible Chat Completions API. The connection is configured through the following environment variables:

- `LIBRALENS_LLM_URL` - required
- `LIBRALENS_LLM_MODEL` - required
- `LIBRALENS_LLM_KEY` - optional, depending on the endpoint

For example:

```bash
export LIBRALENS_LLM_URL="https://api.openai.com/v1"
export LIBRALENS_LLM_MODEL="gpt-5"
export LIBRALENS_LLM_KEY="..."
```

The API key can be omitted for endpoints that do not require authentication, such as some locally hosted models.

## Reference

### Available Methods

LibraLens currently provides the following evaluation methods:

| Method | Requirements | Description |
|---|---|---|
| `text-match` | plain text | Checks whether relevant field values can be found in the corresponding document's plain text. |
| `edit-distance` | gold/platinum records | Compares relevant field values with their corresponding gold or platinum values using the edit distance. |

### Supported MARC Fields

LibraLens currently supports the following MARC 21 fields and subfields. Individual evaluation methods may use only a subset of them.

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