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
- [Concepts](#concepts)
  - [Documents](#documents)
  - [Methods](#methods)
  - [Field Selection](#field-selection)
  - [Runs](#runs)
- [Usage](#usage)
  - [Python Library](#python-library)
  - [Command Line Interface](#command-line-interface)
  - [Results](#results)
- [Evaluation Methods](#evaluation-methods)
  - [Text Match](#text-match)
  - [Edit Distance](#edit-distance)
  - [Common Substring](#common-substring)
  - [Field Validity](#field-validity)
  - [Record Usability](#record-usability)
  - [F1 Score](#f1-score)
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

## Core Concepts

### Documents

The basic unit evaluated by LibraLens is a document. A document can contain:

- an **eval** record to be evaluated (mandatory)
- a **gold** reference record
- a **platinum** reference record
- the plain **text** of the underlying document

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

Fields can be limited globally to control which MARC fields and subfields are considered. If no fields are specified, each method uses all fields and subfields it supports. Complete fields are written using their MARC tag within, while individual subfields use dot notation:

```python
fields=["245", "700.0"]
```

Alternatively, from the command line:

```bash
--fields 245 700.0 710.4
```

Selecting a complete field such as 245 means that every subfield of 245 supported by the respective method is considered. Unsupported fields or subfields are automatically ignored for that method.

### Runs

For more complex evaluations, different methods can use different field selections through runs. With the Python library, runs are defined using `Run`:

```python
runs= [
    Run(method="text-match", fields=["020.a", "245"]),
    Run(method="edit-distance", fields=["100", "700"])
]
```

Alternatively, from the command line, runs are defined in a JSON file:

```json
{
    "runs": [
        {
            "method": "text-match",
            "fields": ["020.a", "245"]
        },
        {
            "method": "edit-distance",
            "fields": ["100", "700"]
        }
    ]
}
```
and passed using:

```bash
--runs runs.json
```

The methods and runs options are mutually exclusive. Global fields cannot be combined with runs. If fields is omitted for a run, the method uses all fields and subfields it supports.

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
    methods=["text-match", "edit-distance", "field-validity"],
    fields=["020.a", "245", "700.0"],
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
    --methods text-match edit-distance field-validity \
    --fields 020.a 245 700.0 \
    --gold gold/ \
    --platinum platinum/ \
    --text text/ \
    --output output/
```

Method-specific configurations can instead be provided through a runs file:

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

Every selected method evaluates every document independently.

Scores are aggregated at three levels:

- **Document score** — mean of the applicable method scores for one document.
- **Method score** — mean score of a method across all documents for which it produced a score.
- **Dataset score** — mean of the document scores.

Scores are normalized between `0.0` and `1.0`, with higher values representing better results. A method may return `None` when it cannot perform an applicable evaluation for a particular document. Such values are excluded from score aggregation.

### Python Results

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
#     "text-match": 0.602,
#     "edit-distance": 1.0
# }

print(ll.document_scores)
# {
#     0: 0.800,
#     1: 0.833,
#     2: 0.786
# }
```

`ll.results` contains the complete per-document and per-method output:

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

The structure of `info` is method-specific and contains the diagnostic information used to understand the resulting score.

### Command-Line Results

The command-line interface prints a summary of the evaluation:

```text
document scores
  0.800 document 0
  0.833 document 1
    n/a document 2
  0.786 document 3

method scores
  0.602 text-match
  1.000 edit-distance

dataset score
  0.801 overall
```

Detailed diagnostic information can be accessed through the Python API or written to disk using `--output`.

## Evaluation Methods

LibraLens currently provides the following methods:

| Method | Requires | Purpose |
|---|---|---|
| [`text-match`](#text-match) | Plain Text | Matches strings from the eval record with the the underlying document plain text. |
| [`edit-distance`](#edit-distance) | Gold and/or Platinum | Compares the eval record to the reference record using edit distance. |
| [`common-substring`](#common-substring) | Gold and/or Platinum | Compares the eval record to the reference record using the longest common substring. |
| [`field-validity`](#field-validity) | — | Checks whether the eval record conforms to known formats and controlled vocabularies. |
| [`record-usability`](#record-usability) | Gold and/or Platinum, [LLM](#llm-configuration) | Applies binary minimum-quality criteria to determine whether the record is usable. |
| [`f1-score`](#f1-score) | Gold and/or Platinum | Computes the f1-score between the eval and reference record for values with unambiguous equality. |

### Text Match

`text-match` checks whether selected MARC values can be found in the plain text of the corresponding document.

This method is intended to evaluate whether bibliographic information recorded in MARC can be supported by the document itself. It does not require a gold or platinum record.

For values such as names, multiple textual representations can be considered so that differences in name ordering and punctuation do not automatically prevent a match.

Each applicable value is classified as matched or unmatched. The score is the proportion of values that could be matched.

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

For person and company names, subfields `.a` and `.b` are treated as parts of the same name. If either is selected, the combined name can therefore be used for matching.

### Edit Distance

`edit-distance` compares selected textual MARC values with their corresponding values in a gold or platinum reference record.

Name fields are first associated with their corresponding reference fields through LibraLens' field mapping. This allows, for example, an eval `700` field to be compared with a corresponding reference `100` field when both represent the same entity.

The method produces a normalized string similarity score between `0.0` and `1.0` for each comparison and averages the applicable comparisons.

For title field `245`, selected subfields are compared individually. When both `.a` and `.b` are selected, an additional comparison of the combined `.a + .b` title is performed.

For person and company names, `.a` and `.b` are treated as a combined name whenever either subfield is selected. This is intentional because the two subfields together may be required to represent the name meaningfully.

**Requires:** gold or platinum

**Supported fields:**

| Field | Subfields |
|---|---|
| `100` | `.a` `.b` |
| `110` | `.a` `.b` |
| `245` | `.a` `.b` `.c` `.d` |
| `700` | `.a` `.b` |
| `710` | `.a` `.b` |

If both gold and platinum records are supplied, comparisons are performed against both available references and their resulting scores are aggregated.

### Common Substring

`common-substring` uses the same record mapping and comparison structure as `edit-distance`, but evaluates string similarity based on common substrings rather than edit distance.

It is useful as an alternative view of textual similarity: two values may share substantial continuous textual content even when insertions, deletions, or additional text affect other similarity measures.

The handling of names and titles is identical to `edit-distance`:

- `.a` and `.b` of person and company names are combined whenever either is selected;
- `245` subfields are compared individually;
- when both `245.a` and `245.b` are selected, their combined value is additionally compared.

**Requires:** gold or platinum

**Supported fields:**

| Field | Subfields |
|---|---|
| `100` | `.a` `.b` |
| `110` | `.a` `.b` |
| `245` | `.a` `.b` `.c` `.d` |
| `700` | `.a` `.b` |
| `710` | `.a` `.b` |

If both gold and platinum records are supplied, comparisons are performed against both available references and their resulting scores are aggregated.

### Field Validity

`field-validity` evaluates whether selected MARC values are structurally or semantically valid according to known rules.

Unlike comparison methods, it does not require a reference record.

The currently implemented checks are:

- `008` positions `00-05` must contain a valid six-digit date;
- `008` positions `35-37` must contain a valid MARC language code;
- `020.a` must contain a valid ISBN-10 or ISBN-13, including a valid checksum;
- `041.a` values must be valid MARC language codes;
- `$4` values in person and company name fields must be valid MARC relator codes.

Each checked value is classified as valid or invalid. The method score is:

```text
valid checks / all checks
```

If no applicable values are present, the method returns no score.

**Requires:** no additional document data

**Supported fields:**

| Field | Subfields / positions |
|---|---|
| `008` | `00-05`, `35-37` |
| `020` | `.a` |
| `041` | `.a` |
| `100` | `.4` |
| `110` | `.4` |
| `700` | `.4` |
| `710` | `.4` |

The validity of a value is deliberately kept separate from whether it is the *correct* value for the document. For example, a valid ISBN can still belong to the wrong publication. Such problems are evaluated by other methods.

### Record Usability

`record-usability` determines whether an eval record satisfies a set of minimum requirements.

Unlike the other scoring methods, it is deliberately binary:

```text
1.0 = usable
0.0 = not usable
```

The method represents **KO criteria**: if any applicable criterion fails, the complete method fails.

The currently implemented criteria are:

#### ISBN match

If the reference record contains an ISBN, the eval ISBN must match it.

ISBN values are normalized before comparison so that formatting differences such as hyphens or spaces do not affect equality.

If the reference contains no ISBN, the criterion passes without requiring one from the eval record.

#### Title presence

The eval record must contain `245.a`.

A missing main title makes the record unusable.

#### Title semantics

The eval `245.a` must retain the semantically important content of the reference `245.a`.

This check is performed using an LLM. The model is asked to identify important words or concepts from the reference title that are missing from the eval title. Articles, prepositions, filler words, and other semantically unimportant differences are not intended to cause failure.

This deliberately differs from string-similarity methods: the objective is not to determine how similar two titles look, but whether the eval title has lost information important enough to change or substantially weaken its meaning.

#### Company presence

If the reference contains at least one company name in the selected company fields, the eval record must also contain at least one company name.

This is a minimum-presence criterion. It does not require the number or identity of company names to be equal.

If the reference contains no company names in the selected fields, the criterion passes.

**Requires:** gold or platinum and an LLM

**Supported fields:**

| Field | Used for |
|---|---|
| `020.a` | ISBN match |
| `110.a`, `110.b` | Company presence |
| `245.a` | Title presence and semantics |
| `710.a`, `710.b` | Company presence |

When both gold and platinum records are available, gold is used as the reference. Platinum is used when no gold record is available.

The diagnostic output lists every executed criterion under either `passed` or `failed`.

### F1 Score

`f1-score` compares sets of MARC values between the eval and reference records using precision, recall, and the F1 score.

This method is intentionally restricted to fields where equality can be established unambiguously. It is therefore not used for free-text values such as names, where deciding whether two differently written values represent the same entity would require an additional matching heuristic.

For each comparison:

```text
precision = true positives / (true positives + false positives)

recall = true positives / (true positives + false negatives)

F1 = 2 × precision × recall / (precision + recall)
```

The method currently evaluates:

- language codes from `041.a`;
- authority identifiers from `$0` in person fields;
- relator codes from `$4` in person fields;
- authority identifiers from `$0` in company fields;
- relator codes from `$4` in company fields.

Person fields `100` and `700` belong to the same comparison group. Company fields `110` and `710` likewise belong to the same comparison group. This reflects that the distinction between main and added entries does not change the identity of the represented person or organization for this evaluation.

**Requires:** gold or platinum

**Supported fields:**

| Field | Subfields |
|---|---|
| `041` | `.a` |
| `100` | `.0` `.4` |
| `110` | `.0` `.4` |
| `700` | `.0` `.4` |
| `710` | `.0` `.4` |

Only selected fields participate in a comparison. For example, selecting only `700.0` compares authority identifiers from `700`, while selecting both `100.0` and `700.0` evaluates identifiers from the combined person-name field group.

If both gold and platinum records are supplied, comparisons are performed against both available references and their resulting scores are aggregated.

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
        01.txt
```
The numbered text files correspond to the records by their order within the `.xml` file, starting at `0`. Leading zeros are optional and do not affect matching. The number of text files must match the number of records.

### LLM Configuration

Some evaluation methods could require an LLM to run. LibraLens supports endpoints exposing an OpenAI-compatible Chat Completions API. The connection is configured using three environment variables:

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