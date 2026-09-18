# LibraLens

<p align="left">
  <img src="assets/logo.png" alt="LibraLens logo" width="400">
</p>

LibraLens is a Python library providing methods for the evaluation of MARC 21 records. It supports records in XML and text format. Records can be evaluated independently or compared against corresponding **gold** and **platinum** reference records:

* **Gold** represents a record based on experienced human-level cataloging.
* **Platinum** represents a maximized record version based on unlimited resources and exceeding general cataloging expectations.

LibraLens is designed as a toolbox, allowing different evaluation methods and MARC fields to be selected depending on the analysis to perform.

## Contents

- [Installation](#installation)
- [Concepts](#concepts)
  - [Documents](#documents)
  - [Methods](#methods)
  - [Fields](#fields)
  - [Runs](#runs)
- [Usage](#usage)
  - [Python Library](#python-library)
  - [Command Line Interface](#command-line-interface)
  - [Results](#results)
- [Evaluation Methods](#evaluation-methods)
  - [Field Validity](#field-validity)
  - [Text Match](#text-match)
  - [Edit Distance](#edit-distance)
  - [Common Substring](#common-substring)
  - [F1 Score](#f1-score)
  - [Record Usability](#record-usability)
- [Configuration](#configuration)
  - [Document Matching](#document-matching)
  - [LLM Configuration](#llm-configuration)
  - [MARC Scope](#marc-scope)

## Installation

LibraLens requires Python 3.10 or later. Using a virtual environment is recommended:

```bash
python -m venv .venv
source .venv/bin/activate
```

Install LibraLens from the project directory:

```bash
pip install .
```

Required Python dependencies are installed automatically.

## Concepts

### Documents

The basic unit evaluated by LibraLens is a document. A document can contain:

- an **eval** record to be evaluated (mandatory)
- a **gold** reference record
- a **platinum** reference record
- the plain **text** of the underlying PDF

Records can be provided as individual files or directories containing multiple files. LibraLens supports `.xml` and `.txt` formats for MARC records. Plain text can be provided as a `.txt` (text is read directly) or `.pdf` (LibraLens PDF text extraction) file. XML files may contain one or multiple records, while text files contain a single record. Corresponding eval, reference, and plain-text data is matched as described in [Document Matching](#document-matching).

The selected evaluation **methods** define what the documents require. For example, `text-match` requires plain text, while comparison methods such as `edit-distance` require a gold or platinum reference record.

### Methods

An evaluation consists of one or more methods. Each method evaluates a particular aspect of the record and returns a normalized score between `0.0` and `1.0`, or `None` when no applicable evaluation can be performed. If no methods are specified, LibraLens runs all available methods.

Specific methods can be selected by passing a list of strings:

```python
methods=["text-match", "edit-distance", "field-validity"]
```

Alternatively, from the command line:

```bash
--methods text-match edit-distance field-validity
```

### Fields

Fields can be limited globally to control which MARC fields and subfields are considered. If no fields are specified, each method uses all fields and subfields it supports. Complete fields are written using their MARC tag (e.g. `100`), while individual subfields use the dot notation (e.g. `245.a`):

```python
fields=["100", "700", "245.a"]
```

Alternatively, from the command line:

```bash
--fields 100 700 245.a
```

Selecting a complete field such as 100 means that every subfield of 100 supported by the respective method is considered. Unsupported fields or subfields are automatically ignored by that method.

### Runs

For more complex evaluations, different methods can use different field selections through runs. With the Python library, runs are defined using `Run`:

```python
runs=[
    Run(method="edit-distance", fields=["100", "700"]),
    Run(method="text-match", fields=["245.a"])
]
```

Alternatively, from the command line, runs are defined in a JSON file:

```json
{
    "runs": [
        {
            "method": "edit-distance",
            "fields": ["100", "700"]
        },
        {
            "method": "text-match",
            "fields": ["245.a"]
        }
    ]
}
```
and passed using:

```bash
--runs runs.json
```

When using runs, methods and fields are configured within each run, so the global `methods` and `fields` options cannot be used. If `fields` are omitted from a run, the method uses all fields and subfields it supports.

## Usage

LibraLens can be used either directly as a Python library or through the command-line interface. Both interfaces provide the same evaluation functionality.

### Python Library

The `LibraLens` class provides the main entry point to the library. At minimum, an eval file or directory must be provided:

```python
from libralens import LibraLens

ll = LibraLens(eval="records/")
results = ll.evaluate()
```

Methods and fields can be selected as needed, while gold, platinum, and plain-text data can be provided for methods that require them:

```python
from libralens import LibraLens

ll = LibraLens(
    eval="records/",
    methods=["edit-distance", "text-match"],
    fields=["100", "700", "245.a"],
    gold="gold/",
    platinum="platinum/",
    text="text/",
    output="output/"
)

results = ll.evaluate()
```

Method-specific field selections can be configured using `Run`:

```python
from libralens import LibraLens, Run

ll = LibraLens(
    eval="records/",
    runs=[
        Run(method="edit-distance", fields=["100", "700"]),
        Run(method="text-match", fields=["245.a"])
    ],
    gold="gold/",
    platinum="platinum/",
    text="text/",
    output="output/"
)

results = ll.evaluate()
```

The optional `output` parameter writes detailed evaluation results and the corresponding document data to disk.

### Command Line Interface

The same evaluation can be performed through the `libralens` command:

```bash
libralens \
    --eval records/ \
    --methods edit-distance text-match \
    --fields 100 700 245.a \
    --gold gold/ \
    --platinum platinum/ \
    --text text/ \
    --output output/
```

Method-specific field selections can be provided through a JSON file:

```bash
libralens --eval records/ --platinum platinum/ --text text/ --runs runs.json
```

Short forms are available for the main command-line options:

| Option | Short form |
|---|---|
| `--eval` | `-e` |
| `--methods` | `-m` |
| `--runs` | `-r` |
| `--fields` | `-f` |
| `--gold` | `-g` |
| `--platinum` | `-p` |
| `--text` | `-t` |
| `--output` | `-o` |

Run `libralens --help` for the complete command-line reference.

### Results

Every selected method evaluates every document independently. Scores are aggregated at three levels:

- **Document score** — mean of the applicable method scores for one document.
- **Method score** — mean score of a method across all documents for which it produced a score.
- **Dataset score** — mean of the document scores.

Scores are normalized between `0.0` and `1.0`, with higher values representing better results. A method may return `None` when it cannot perform an applicable evaluation for a particular document.

#### Python Library

After calling `evaluate()`, results are available directly from the `LibraLens` instance:

```python
ll.evaluate()

ll.score
ll.method_scores
ll.document_scores
ll.results
```

For example:

```python
print(ll.score)
# 0.801

print(ll.method_scores)
# {
#     "edit-distance": 0.917,
#     "text-match": 0.685
# }

print(ll.document_scores)
# {
#     0: 0.800,
#     1: 0.833,
#     2: None,
#     3: 0.770
# }
```

`ll.results` contains the complete per-document and per-method output:

```python
[
    {
        "id": 0,
        "score": 0.8,
        "methods": {
            "edit-distance": {
                "score": 0.9,
                "info": {
                    ...
                }
            },
            "text-match": {
                "score": 0.7,
                "info": {
                    ...
                }
            }
        }
    }
]
```

The structure of `info` is method-specific and contains the diagnostic information used to understand the resulting score.

#### Command Line Interface

The command-line interface prints a summary of the evaluation:

```text
document scores
  0.800 document 0
  0.833 document 1
    n/a document 2
  0.770 document 3

method scores
  0.917 edit-distance
  0.685 text-match

dataset score
  0.801 overall
```

Detailed diagnostics can be accessed on disk by passing the `--output` option.

## Evaluation Methods

LibraLens currently provides the following methods:

| Method | Requires | Purpose |
|---|---|---|
| [`field-validity`](#field-validity) |  | Checks whether the eval record conforms to known formats and controlled vocabularies. |
| [`text-match`](#text-match) | Plain Text | Matches strings from the eval record with the underlying PDF plain text. |
| [`edit-distance`](#edit-distance) | Gold and/or Platinum | Compares the eval record to the reference record using edit distance. |
| [`common-substring`](#common-substring) | Gold and/or Platinum | Compares the eval record to the reference record using the longest common substring. |
| [`f1-score`](#f1-score) | Gold and/or Platinum | Computes the F1 score between the eval and reference record for values with unambiguous equality. |
| [`record-usability`](#record-usability) | Gold and/or Platinum, [LLM](#llm-configuration) | Applies binary minimum-quality criteria to determine whether the record is usable. |

### Field Validity

`field-validity` checks whether the eval record conforms to known formats and controlled vocabularies.

The currently implemented checks are:

- `008` positions `00-05` must contain a valid six-digit date
- `008` positions `35-37` must contain a valid language code
- `020.a` must contain a valid ISBN-10 or ISBN-13, including a valid checksum
- `041.a` values must be valid language codes
- `.4` values in person and corporate name fields must be valid relator codes

Each checked value is classified as valid or invalid. The method score is:

```text
valid checks / all checks
```

**Requires:** no additional document data

**Supported fields:**

| Field | Subfields |
|---|---|
| `008` |      |
| `020` | `.a` |
| `041` | `.a` |
| `100` | `.4` |
| `110` | `.4` |
| `700` | `.4` |
| `710` | `.4` |

### Text Match

`text-match` checks whether strings from the eval record can be found in the underlying PDF plain text.

Before matching, both the MARC values and the plain text are normalized using Unicode NFKC normalization, lowercasing, and whitespace normalization. Consecutive whitespace is reduced to a single space, and leading or trailing whitespace is removed. Some values are represented by multiple alternative strings before matching:

- `020.a`: the original ISBN, a compact version without spaces or hyphens, and a version using spaces instead of hyphens
- `100` and `700`: subfields `.a` and `.b` are combined, and multiple name variants are generated to account for differences in name ordering and punctuation
- `110` and `710`: subfields `.a` and `.b` are combined into one corporate name
- `245`: title, subtitle, and parallel title are matched separately
- `264`: locations, publishers, and years are matched separately

A logical value counts as matched if **at least one** of its generated variants can be found in the plain text. For example, the following person-name variants belong to one logical value:

```text
Jobs Steve
Jobs, Steve
Steve Jobs
Steve, Jobs
```

If any one of them is found, the name is counted as matched. Each applicable logical value is classified as matched or unmatched. The method score is:

```text
matched values / all checked values
```

**Requires:** plain text

**Supported fields:**

| Field | Subfields |
|---|---|
| `020` | `.a` |
| `100` | `.a` `.b` |
| `110` | `.a` `.b` |
| `245` | `.a` `.b` `.d` |
| `264` | `.a` `.b` `.c` |
| `700` | `.a` `.b` |
| `710` | `.a` `.b` |

For `100`, `110`, `700`, and `710`, subfields `.a` and `.b` are treated as parts of the same name. If either is selected, the combined name is considered.

### Edit Distance

`edit-distance` compares the eval record to the reference record using edit distance.

Each comparison produces a normalized similarity score between `0.0` and `1.0` based on the Levenshtein method, and the method score is the mean of all applicable comparison scores.

Person fields `100` and `700` can be compared with one another when they represent the same person. The same applies to corporate fields `110` and `710`. For these name fields, subfields `.a` and `.b` are treated as one combined name whenever either is selected.

For field `245`, selected subfields are compared individually. When both `.a` and `.b` are selected, an additional comparison of the combined `.a + .b` title is performed.

The method score is:

```text
sum of comparison scores / number of comparisons
```

**Requires:** gold or platinum

**Supported fields:**

| Field | Subfields |
|---|---|
| `100` | `.a` `.b` |
| `110` | `.a` `.b` |
| `245` | `.a` `.b` `.c` `.d` |
| `700` | `.a` `.b` |
| `710` | `.a` `.b` |

If both gold and platinum records are supplied, comparisons are performed against both references and the resulting reference scores are averaged.

### Common Substring

`common-substring` compares the eval record to the reference record using the longest common substring.

Each comparison produces a normalized similarity score between `0.0` and `1.0`, based on the length of the longest continuous substring shared by both values, and the method score is the mean of all applicable comparison scores.

Person fields `100` and `700` can be compared with one another when they represent the same person. The same applies to corporate fields `110` and `710`. For these name fields, subfields `.a` and `.b` are treated as one combined name whenever either is selected.

For field `245`, selected subfields are compared individually. When both `.a` and `.b` are selected, an additional comparison of the combined `.a + .b` title is performed.

The method score is:

```text
sum of comparison scores / number of comparisons
```

**Requires:** gold or platinum

**Supported fields:**

| Field | Subfields |
|---|---|
| `100` | `.a` `.b` |
| `110` | `.a` `.b` |
| `245` | `.a` `.b` `.c` `.d` |
| `700` | `.a` `.b` |
| `710` | `.a` `.b` |

If both gold and platinum records are supplied, comparisons are performed against both references and the resulting reference scores are averaged.

### F1 Score

`f1-score` computes the F1 score between the eval and reference record for values with unambiguous equality.

The method is intentionally restricted to values that can be compared exactly, without fuzzy matching or additional heuristics. It currently compares language codes from `041.a`, authority identifiers from `.0`, and relator codes from `.4`.

Values are treated as sets. For each comparison, values present in both eval and reference are true positives, values only present in eval are false positives, and values only present in the reference are false negatives:

```text
precision = true positives / (true positives + false positives)

recall = true positives / (true positives + false negatives)

F1 = 2 × true positives / (2 × true positives + false positives + false negatives)
```

Person fields `100` and `700` are combined into one comparison group, while corporate fields `110` and `710` form a second group. Only selected fields and subfields participate in a comparison. Comparisons for which both eval and reference contain no values are omitted.

The method score is the mean of all applicable F1 comparison scores.

**Requires:** gold or platinum

**Supported fields:**

| Field | Subfields |
|---|---|
| `041` | `.a` |
| `100` | `.0` `.4` |
| `110` | `.0` `.4` |
| `700` | `.0` `.4` |
| `710` | `.0` `.4` |

If both gold and platinum records are supplied, comparisons are performed against both references and the resulting reference scores are averaged.

### Record Usability

`record-usability` applies binary minimum-quality criteria to determine whether the record is usable.

The method evaluates a set of KO criteria and returns:

```text
1.0 = all applicable criteria passed
0.0 = at least one applicable criterion failed
```

The currently implemented criteria are:

- **ISBN match (`020.a`)**: if the reference contains an ISBN, the eval ISBN must match it after normalization. If the reference contains no ISBN, the criterion passes.
- **Title presence (`245.a`)**: the eval record must contain a main title.
- **Title semantics (`245.a`)**: the eval title must retain the semantically important content of the reference title. An LLM identifies important missing words or concepts while ignoring semantically unimportant differences such as articles, prepositions, and filler words.
- **Corporate presence (`110`, `710`)**: if the reference contains at least one corporate name in the selected fields, the eval record must also contain at least one. The number and identity of corporate names do not need to match.

Every executed criterion is listed in the diagnostic output under either `passed` or `failed`.

**Requires:** gold or platinum and an [LLM](#llm-configuration)

**Supported fields:**

| Field | Subfields |
|---|---|
| `020` | `.a` |
| `110` | `.a` `.b` |
| `245` | `.a` |
| `710` | `.a` `.b` |

For `110` and `710`, subfields `.a` and `.b` are treated as parts of the same corporate name. If either is selected, the combined name is considered.

When both gold and platinum records are available, gold is used as the reference. Platinum is used only when no gold record is available.


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
    record1.pdf
```
Plain text files use the same base filename as the corresponding record and may use either the `.txt` (text is read directly) or `.pdf` (LibraLens PDF text extraction) extension. When corresponding `.xml` files contain multiple records, eval, gold, and platinum records are paired by their order within the file. 

> **Caution:** Record order must be consistent across corresponding eval, gold and platinum files. LibraLens does not verify that records at the same position represent the same bibliographic document. Incorrect ordering may therefore cause records to be evaluated against the wrong gold or platinum standard.

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
        01.pdf
```
The numbered plain text files correspond to the records by their order within the `.xml` file, starting at `0`. Leading zeros are optional and do not affect matching. The number of text sources must match the number of records.

### LLM Configuration

Some evaluation methods require access to an LLM. LibraLens supports endpoints exposing an OpenAI-compatible Chat Completions API. The connection is configured using three environment variables:

| Variable | Required | Description |
|---|---|---|
| `LIBRALENS_LLM_URL` | yes | Base URL |
| `LIBRALENS_LLM_MODEL` | yes | Model Identifier |
| `LIBRALENS_LLM_KEY` | no | API Key |

For example:
```bash
export LIBRALENS_LLM_URL="https://api.openai.com/v1"
export LIBRALENS_LLM_MODEL="gpt-5"
export LIBRALENS_LLM_KEY="..."
```

The API key can be omitted for endpoints that do not require authentication, such as some locally hosted models.

### MARC Scope

LibraLens currently considers the following MARC 21 data:

```
008, 020.a, 041.a, 100, 110, 245, 264, 300, 490, 700, 710
```

This set defines the overall MARC data considered by LibraLens and constrains which data is written to disk when using the `--output` option. Each evaluation method supports its own subset, documented in the corresponding method section.