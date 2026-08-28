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
    text="text/",
    output="output/"
)

results = ll.run()
```

The parameters `fields`, `gold`, `platinum`, `text` and `output` are optional. If `fields` is omitted, all supported fields are considered by default.

For more complex evaluations, different fields can be selected for each method using `Run`:

```python
from libralens import LibraLens, Run

ll = LibraLens(
    eval="records/",
    runs=[
        Run(
            method="text-match",
            fields=["020", "245", "264"]
        ),
        Run(
            method="edit-distance",
            fields=["100", "110", "700", "710"]
        )
    ],
    gold="gold/",
    platinum="platinum/",
    text="text/"
)

results = ll.run()
```

The `methods` and `runs` parameters are mutually exclusive. When using `runs`, fields are configured individually for each run and the global `fields` parameter cannot be used. If `fields` is omitted from a `Run`, all supported fields are considered for that run.

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

For more complex evaluations, different fields can be selected for each method through a JSON runs file:

```json
{
    "runs": [
        {
            "method": "text-match",
            "fields": ["020", "245", "264"]
        },
        {
            "method": "edit-distance",
            "fields": ["100", "110", "700", "710"]
        }
    ]
}
```

Run the configuration using:

```bash
libralens --eval records/ --runs runs.json
```

The `--methods` and `--runs` options are mutually exclusive. When using `--runs`, fields are configured individually for each run and `--fields` cannot be used. If `fields` is omitted from a run, all supported fields are considered for that run.

Provide corresponding gold and platinum standards:

```bash
libralens --eval records/ --methods text-match --gold gold/ --platinum platinum/
```

Certain methods require the corresponding document's plain text:

```bash
libralens --eval records/ --methods text-match --text text/
```

Export detailed evaluation results and the corresponding document data to an output directory:
```bash
libralens --eval records/ --methods text-match --text text/ --output results/
```
The output directory contains a `results.json` file with detailed scores and diagnostic information, as well as the corresponding eval, gold, platinum, and plain-text data for each document.

The short forms `-e`, `-m`, `-r`, `-f`, `-g`, `-p`, `-t` and `-o` can be used instead of their corresponding long options. Check `--help` for more info.

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
# {0: 0.8, 1: 0.833, 2: 0.786, 3: 0.786}
```

`ll.results` contains the detailed results organized by document and method:

```python
[
    {
        "id": 0,
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

Detailed diagnostic information is available through the Python library or can be exported using the `--output` option.

## Configuration

### Document Matching

When individual files are provided explicitly for eval, gold, platinum, or plain text, their filenames do not need to match. The provided files are considered to belong to the same document. When directories are provided, corresponding eval, gold, platinum, and plain-text data is matched through base filenames. For example:

```
eval/
    record0.xml
    record1.xml
gold/
    record0.xml
    record1.xml
platinum/
    record0.xml
    record1.xml
text/
    record0.txt
    record1.txt
```

Plain-text files use the same base filename but always use the .txt extension. When corresponding .xml files contain multiple records, eval, gold, and platinum records are paired by their order within the file. 

**Caution**: Record order must be consistent across corresponding eval, gold and platinum files. LibraLens does not verify that records at the same position represent the same bibliographic document. Incorrect ordering may therefore cause records to be evaluated against the wrong gold or platinum standard.

For a multi-record `.xml` file, the corresponding plain text is provided through a directory with the same base filename:

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
| `edit-distance` | gold and/or platinum | Compares relevant field values with their corresponding gold or platinum values using the edit distance. |

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