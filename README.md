# LibraLens

<p align="left">
  <img src="assets/logo.png" alt="LibraLens logo" width="400">
</p>

LibraLens is a Python library providing methods for the evaluation of MARC 21 records. It supports records in XML and text format. Records can be evaluated independently or compared against corresponding **gold** and **platinum** reference records:

* **Gold** represents a record based on experienced human-level cataloging.
* **Platinum** represents a maximized record version exceeding general cataloging expectations.

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
  - [Common Substring](#common-substring)
  - [Edit Distance](#edit-distance)
  - [F1 Score](#f1-score)
  - [Subfield Cardinality](#subfield-cardinality)
  - [Record Usability](#record-usability)
- [Configuration](#configuration)
  - [Document Matching](#document-matching)
  - [LLM Configuration](#llm-configuration)
  - [MARC Scope](#marc-scope)

## Installation

LibraLens was developed using Python 3.13. Using a virtual environment is recommended:

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

Selecting a complete field (e.g. 100) means that every subfield of 100, supported by the respective method, is considered. Unsupported fields or subfields are automatically ignored by that method.

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

When using runs, methods and fields are configured within each run, so the global `methods` and `fields` options cannot be used. If `fields` is omitted from a run, the method uses all fields and subfields it supports.

## Usage

LibraLens can be used either directly as a Python library or through the command-line interface. Both interfaces provide the same functionality.

### Python Library

The `LibraLens` class provides the main entry point to the library. At minimum, an eval file/directory must be provided:

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
    text="text/"
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

Scores are normalized between `0.0` and `1.0`, with higher values representing better results. A method may return `None` when it cannot evaluate a particular document.

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

The structure of `info` is method-specific and contains the information used to understand the resulting score.

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

LibraLens currently provides the following seven methods:

| Method | Requires | Purpose |
|---|---|---|
| [`field-validity`](#field-validity) |  | Checks whether the eval record conforms to known formats and controlled vocabularies. |
| [`text-match`](#text-match) | Plain Text | Matches strings from the eval record with the underlying PDF plain text. |
| [`common-substring`](#common-substring) | Gold and/or Platinum | Compares the eval record to the reference record using the longest common substring. |
| [`edit-distance`](#edit-distance) | Gold and/or Platinum | Compares the eval record to the reference record using edit distance. |
| [`f1-score`](#f1-score) | Gold and/or Platinum | Computes the F1 score between the eval and reference record for values with unambiguous equality. |
| [`subfield-cardinality`](#subfield-cardinality) | Gold and/or Platinum | Compares the cardinality of selected fields and subfields in the eval and reference records. |
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

`text-match` matches strings from the eval record with the underlying PDF plain text.

Before matching, both the MARC values and the plain text are normalized using Unicode NFKC normalization, lowercasing, and whitespace normalization. Consecutive whitespaces are reduced to a single space, and leading or trailing whitespaces are removed. Some values are represented by multiple alternative strings before matching:

- `020.a`: the original ISBN, a compact version without spaces or hyphens, and a version using spaces instead of hyphens
- `094.a`: the value is matched directly
- `100` and `700`: subfields `.a` and `.b` are concatenated into one person name, and multiple name variants are generated to account for differences in name ordering and punctuation
- `110` and `710`: subfields `.a` and `.b` are concatenated, in that order, into one corporate name
- `245`: title, subtitle, and parallel title are matched separately
- `264`: locations, publishers, and years are matched separately

A logical value counts as matched if **at least one** of its generated variants can be found in the plain text. For example, the following person-name variants belong to one logical value:

```text
Doe John
Doe, John
John Doe
John, Doe
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
| `094` | `.a` |
| `100` | `.a` `.b` |
| `110` | `.a` `.b` |
| `245` | `.a` `.b` `.d` |
| `264` | `.a` `.b` `.c` |
| `700` | `.a` `.b` |
| `710` | `.a` `.b` |

For `100`, `110`, `700`, and `710`, subfields `.a` and `.b` are treated as parts of the same name. If either is selected, the combined `.a + .b` name is considered. For corporate fields `110` and `710`, this is a direct concatenation of the available `.a` and `.b` values in that order; no person-name permutations are generated.

### Common Substring

`common-substring` compares strings from the eval record with corresponding strings from a gold or platinum reference record using the longest common substring.

Each comparison produces a normalized similarity score between `0.0` and `1.0`, based on the length of the longest continuous substring shared by both values. Same as the [`edit-distance`](#edit-distance) method, **only values for which a comparison can be established contribute to the score**. Missing, extra, or otherwise unmatched values are omitted rather than assigned a score of `0.0`. The method therefore measures the similarity of comparable values rather than record completeness or cardinality. Differences in cardinality can instead be evaluated using [`subfield-cardinality`](#subfield-cardinality).

Person fields (`100` and `700`) are mapped across the eval and reference records according to the person they represent, same as corporate fields (`110` and `710`). A field may therefore be mapped across tags (e.g. an eval `710` could be compared to a reference `110`).

For person and corporate fields, `.a` and `.b` are concatenated into a single string before the longest common substring is calculated. The available values are concatenated in `.a + .b` order. For example:

```text
710 $a Example Organization $b Research Department
```

is compared as the equivalent of:

```text
Example Organization Research Department
```

`094.a` is compared directly when a value is available in both records.

For field `245`, selected subfields are compared individually when a value is available in both records. When both `.a` and `.b` are selected, an additional comparison of the combined `.a + .b` title is performed.

The method score is:

```text
sum of applicable comparison scores / number of applicable comparisons
```

**Requires:** gold or platinum

**Supported fields:**

| Field | Subfields |
|---|---|
| `094` | `.a` |
| `100` | `.a` `.b` |
| `110` | `.a` `.b` |
| `245` | `.a` `.b` `.c` `.d` |
| `700` | `.a` `.b` |
| `710` | `.a` `.b` |

If both gold and platinum records are supplied, comparisons are performed against both references and the resulting reference scores are averaged.

### Edit Distance

`edit-distance` compares strings from the eval record with corresponding strings from a gold or platinum reference record using the normalized Levenshtein similarity metric.

The method follows the same comparison procedure as [`common-substring`](#common-substring), including field mapping, name construction, handling of missing and unmatched values, and score aggregation. The only difference is the string similarity metric istelf: `edit-distance` uses Levenshtein similarity instead of the longest common substring.

Each string comparison produces a normalized similarity score between `0.0` and `1.0`.

**Requires:** gold or platinum

**Supported fields:**

| Field | Subfields |
|---|---|
| `094` | `.a` |
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

Person fields `100` and `700` are combined into one comparison group, while corporate fields `110` and `710` form a second group. Unlike `edit-distance` and `common-substring`, the F1 comparison operates on sets of selected values rather than mapped pairs of field occurrences. Extra and missing values therefore directly affect precision and recall.

Only selected fields and subfields participate in a comparison. Comparisons for which both eval and reference contain no values are omitted.

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

### Subfield Cardinality

`subfield-cardinality` evaluates whether the eval record contains the same amount of selected MARC data as a gold or platinum reference record.

The method operates on the subfield level (except for controlfields) and considers only cardinality. For example, if both records contain exactly one `245.a`, the score equals `1.0` (subfield abscence can be desired). In general, the score is computed as the ratio between the smaller and larger count. If both counts are `0`, the score is `1.0`. The actual content of the values does not affect the score and can instead be evaluated using other methods. 

#### Standard fields

For fields other than `100`, `110`, `700` and `710`, occurrences of each selected subfield are counted globally in the eval and reference records, for example:

```text
Eval:
264 $a Luxembourg
264 $a Paris

Reference:
264 $a Luxembourg
```

produces the following cardinality comparison for `264.a`:

```text
eval count = 2
reference count = 1
score = 0.5
```

#### Mapped fields

Person fields `100/700` are treated as one group, same as the corporate fields `110/710`. Field occurrences are mapped between the eval and reference groups based on their names (i.e. a mapping may cross MARC tags within the group). Cardinality is then evaluated **within each mapped pair**.

For example:

```text
Eval:
100 $a Alice $0 X
700 $a Bob

Reference:
700 $a Alice $0 X
700 $a Bob $0 Y
```

For subfield `.0`, the mapped comparisons and final score are:

```text
Alice ↔ Alice: 1 vs 1 → 1.0
Bob   ↔ Bob:   0 vs 1 → 0.0

score = (1.0 + 0.0) / 2 = 0.5
```

A mapped pair also contributes when both occurrences contain zero instances of the selected subfield. For example:

```text
Eval:
100 $a Alice

Reference:
700 $a Alice
```

produces `0` versus `0` for subfield `.0`, with a score of `1.0`.

Unmatched person/corporate fields are also considered, but **only when the unmatched field contains the selected subfield**, regardless of whether it occurs in the eval or reference record. For example, for `.0` the Bob field contributes a score of `0.0`:

```text
Eval:
700 $a Alice
700 $a Bob $0 X

Reference:
700 $a Alice
```

If there are no fields at all on either side for a person/corporate group, cardinality is still considered as correct (0 vs 0) with a score of `1.0`. 

#### Aggregation

For standard fields, there is a single cardinality comparison producing the final score for the subfield. For mapped fields, a selected subfield can produce multiple comparisons: one for every mapped occurrence and, where applicable, additional comparisons for unmatched occurrences. The subfield score is the mean of these comparison scores:

```text
sum of subfield scores / number of subfields
```

**Requires:** gold or platinum

**Supported fields:**

| Field | Subfields |
|---|---|
| `008` | |
| `020` | `.a` |
| `041` | `.a` |
| `094` | `.a` |
| `100` | `.a` `.b` `.d` `.0` `.e` `.4` |
| `110` | `.a` `.b` `.d` `.0` `.e` `.4` |
| `245` | `.a` `.b` `.c` `.d` |
| `264` | `.a` `.b` `.c` |
| `300` | `.a` `.b` |
| `490` | `.a` |
| `700` | `.a` `.b` `.d` `.0` `.e` `.4` |
| `710` | `.a` `.b` `.d` `.0` `.e` `.4` |

For cardinality purposes, selecting a supported subfield from `100` or `700` evaluates that subfield across the combined `100/700` person group. The same applies to the combined `110/710` corporate group.

If both gold and platinum records are supplied, cardinality is evaluated independently against each reference and the resulting reference scores are averaged.

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

For the corporate-presence criterion, `110` and `710` subfields `.a` and `.b` are treated as parts of the same corporate name and concatenated in `.a + .b` order. If either is selected, the combined name is considered. This criterion tests for the presence of a corporate name; it does not compare the identity or number of corporate names between records.

When both gold and platinum records are available, gold is used as the reference. Platinum is used only when no gold record is available.

## Configuration

### Document Matching

When individual files are provided explicitly for eval, gold, platinum, or plain text, their filenames do not need to match. The files are always considered to belong to the same document. When directories are provided, corresponding eval, gold, platinum, and plain-text data is matched through base filenames. For example:

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
Plain text files use the same base filename as the corresponding record and use either the `.txt` (text is read directly) or the `.pdf` (LibraLens PDF text extraction) extension. When corresponding `.xml` files contain multiple records, eval, gold, and platinum records are paired based on their order within the file. 

> **Caution:** Record order must be consistent across corresponding eval, gold and platinum files. LibraLens does not verify that records at the same position represent the same bibliographic document. Incorrect ordering could therefore cause records to be evaluated against the wrong gold or platinum reference.

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
The numbered plain text files correspond to the records by their order within the `.xml` file, starting at `0`. Leading zeros are optional and do not affect matching. The number of text files must match the number of records.

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

The API key can be omitted, depending on the used model (e.g. locally hosted).

### MARC Scope

Aggregating all methods, LibraLens currently supports the following MARC 21 fields and subfields:

```
008
020.a
041.a
094.a
100.a, 100.b, 100.d, 100.0, 100.e, 100.4
110.a, 110.b, 110.d, 110.0, 110.e, 110.4
245.a, 245.b, 245.c, 245.d
264.a, 264.b, 264.c
300.a, 300.b
490.a
700.a, 700.b, 700.d, 700.0, 700.e, 700.4
710.a, 710.b, 710.d, 710.0, 710.e, 710.4
```

This set also defines which data is written to disk when using the `--output` option.