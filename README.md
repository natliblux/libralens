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
  - [Grouping](#grouping)
  - [Mapping](#mapping)
  - [Selections](#selections)
  - [Runs](#runs)
- [Usage](#usage)
  - [Python Library](#python-library)
  - [Command Line Interface](#command-line-interface)
  - [Results](#results)
- [Evaluation Methods](#evaluation-methods)
  - [Field Validity](#method-field-validity)
  - [Text Match](#method-text-match)
  - [Common Substring](#methods-value-comparisons)
  - [Edit Distance](#methods-value-comparisons)
  - [F1 Score](#methods-set-comparisons)
  - [Precision Score](#methods-set-comparisons)
  - [Recall Score](#methods-set-comparisons)
  - [Subfield Cardinality](#method-subfield-cardinality)
  - [Record Usability](#method-record-usability)
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

The selected evaluation **methods** define what the documents require. For example, `text-match` requires plain text, while comparison methods such as `edit-distance` require a reference record (gold and/or platinum).

### Methods

An evaluation consists of one or more methods. Each method evaluates a particular aspect of the record and returns a normalized score between `0.0` and `1.0`, or `None` when no applicable evaluation can be performed. If no methods are specified, LibraLens runs all available methods. Specific methods can be selected by passing a list of strings:

```python
methods=["edit-distance", "text-match"]
```

Alternatively, from the command line:

```bash
--methods edit-distance text-match
```

### Fields

LibraLens supports a selection of MARC 21 fields and subfields, depending on the evaluation method. The complete list is available [here](#marc-scope). For controlfield `008`, LibraLens treats positions `00-05` and `35-37` as virtual subfields, which are handled like regular MARC subfields during evaluation.

### Grouping

The person fields `100/700` and the corporate fields `110/710` are each treated as one group, which allows related information to be evaluated together. For example, person names in `100` and `700` are treated as belonging to the same group, rather than as two separate categories.

### Mapping

For certain methods, LibraLens maps corresponding field occurrences between eval and reference records. Mapping applies to person (`100/700`), corporate (`110/710`), and `264` fields. Person and corporate mappings may cross MARC tags within their respective groups, while 264 occurrences are mapped only to other 264 occurrences.

```text
Eval:
100 $a Alice
700 $a Bob

Reference:
700 $a Alice
100 $a Bob

Mappings:
100 Alice ↔ 700 Alice
700 Bob   ↔ 100 Bob
```

Mapping allows evaluation methods to compare corresponding occurrences even when their order, cardinality, or for grouped fields, their MARC tags differ.

### Selections

Fields can be limited globally to control which MARC fields and subfields are considered. If no fields are specified, each method uses all fields and subfields it supports. Complete fields are selected using their MARC tag (e.g. `245`), while individual subfields use dot notation (e.g. `700.a`). Virtual subfields (`008`) use the same notation (e.g. `008.35-37`). For example:

```python
fields=["245", "700.a"]
```

Alternatively, from the command line:

```bash
--fields 245 700.a
```

Selecting a complete field (e.g. `245`) includes all subfields or position ranges supported by the respective method. For grouped person (`100/700`) and corporate (`110/710`) fields, selecting a subfield automatically includes the same subfield across the entire group (selecting `700.a` also selects `100.a`). Unsupported fields and subfields are automatically ignored by LibraLens.


### Runs

For more complex evaluations, different methods can use different field selections through runs. With the Python library, runs are defined using `Run`:

```python
runs=[
    Run(method="edit-distance", fields=["245", "700.a"]),
    Run(method="text-match", fields=["020.a"])
]
```

Alternatively, from the command line, runs are defined in a JSON file:

```json
{
    "runs": [
        {
            "method": "edit-distance",
            "fields": ["245", "700.a"]
        },
        {
            "method": "text-match",
            "fields": ["020.a"]
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

LibraLens currently provides the following nine methods:

| Method | Requires | Purpose |
|---|---|---|
| [`field-validity`](#method-field-validity) |  | Checks whether the eval record conforms to known formats and controlled vocabularies. |
| [`text-match`](#method-text-match) | Plain Text | Matches strings from the eval record with the underlying PDF plain text. |
| [`common-substring`](#methods-value-comparisons) | Reference Record | Compares the eval record to the reference record using the longest common substring. |
| [`edit-distance`](#methods-value-comparisons) | Reference Record | Compares the eval record to the reference record using edit distance. |
| [`f1-score`](#methods-set-comparisons) | Reference Record | Computes the F1 score between the eval and reference record for values with unambiguous equality. |
| [`precision-score`](#methods-set-comparisons) | Reference Record | Computes the precision score between the eval and reference record for values with unambiguous equality. |
| [`recall-score`](#methods-set-comparisons) | Reference Record | Computes the recall score between the eval and reference record for values with unambiguous equality. |
| [`subfield-cardinality`](#method-subfield-cardinality) | Reference Record | Compares the cardinality of selected fields and subfields in the eval and reference records. |
| [`record-usability`](#method-record-usability) | Reference Record and [LLM](#llm-configuration) | Applies binary minimum-quality criteria to determine whether the record is usable. |

Methods requiring a reference record can use gold, platinum, or both. If both are supplied, the method is evaluated independently against each reference, and the two resulting scores are averaged.

### Method: Field Validity

`field-validity` checks whether the eval record conforms to known formats and controlled vocabularies.

The currently implemented checks are:

- `008.00-05` must contain a valid six-digit date
- `008.35-37` must contain a valid language code
- `020.a` must contain a valid ISBN-10 or ISBN-13, including a valid checksum
- `041.a` values must be valid language codes
- `.4` values in person and corporate name fields must be valid relator codes

Each checked value is classified as valid or invalid. The method score is:

```text
valid checks / all checks
```

**Requires:** no additional document data

**Supports:**

| Field | Subfields |
|---|---|
| `008` | `.00-05` `.35-37` |
| `020` | `.a` |
| `041` | `.a` |
| `100` | `.4` |
| `110` | `.4` |
| `700` | `.4` |
| `710` | `.4` |

[↑ Back to all evaluation methods](#evaluation-methods)

### Method: Text Match

`text-match` matches strings from the eval record with the underlying PDF plain text.

Before matching, both the MARC values and the plain text are normalized using Unicode NFKC normalization, lowercasing, and whitespace normalization. Consecutive whitespaces are reduced to a single space, and leading or trailing whitespaces are removed. Some values are represented by multiple alternative strings before matching:

- `020.a`: the original ISBN, a compact version without spaces or hyphens, and a version using spaces instead of hyphens
- `100/700`: subfields `.a` and `.b` are concatenated into one person name, and multiple name variants are generated to account for differences in name ordering and punctuation
- `110/710`: subfields `.a` and `.b` are concatenated, in that order, into one corporate name
- `245`: title, subtitle, and parallel title are matched separately
- `264`: locations, publishers, and years are matched separately
- `490.a`: the value is matched separately

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

**Supports:**

| Field | Subfields |
|---|---|
| `020` | `.a` |
| `100` | `.a` `.b` |
| `110` | `.a` `.b` |
| `245` | `.a` `.b` `.d` |
| `264` | `.a` `.b` `.c` |
| `490` | `.a` |
| `700` | `.a` `.b` |
| `710` | `.a` `.b` |

[↑ Back to all evaluation methods](#evaluation-methods)

### Methods: Value Comparisons

The methods `common-substring` and `edit-distance` compare strings from the eval record with corresponding strings from a gold or platinum reference record. Each string comparison produces a normalized similarity score between `0.0` and `1.0`:

-   `common-substring` uses the length of the longest continuous substring shared by both values.
-   `edit-distance` uses the normalized Levenshtein similarity.

For both methods, **only values for which a comparison can be established contribute to the score**. Missing, extra, or otherwise unmatched values are omitted rather than assigned a score of `0.0`. The methods therefore measure the similarity of comparable values rather than record completeness or cardinality. Differences in cardinality can instead be evaluated using [`subfield-cardinality`](#method-subfield-cardinality).


For person and corporate fields, `.a` and `.b` are concatenated into a single string before the similarity is calculated. The available values are concatenated in `.a + .b` order. For example:

``` text
710 $a Example Organization $b Research Department
```

is compared as the equivalent of:

``` text
Example Organization Research Department
```

For field `245`, selected subfields are compared individually when a value is available in both records. When both `.a` and `.b` are selected, an additional comparison of the combined `.a + .b` title is performed. `490.a` is compared individually as well. For field `264`, subfields `.a`, `.b`, and `.c` are compared individually within corresponding mapped occurrences.

The method score is:

``` text
sum of applicable comparison scores / number of applicable comparisons
```

**Requires:** gold or platinum

**Supports:**

| Field | Subfields |
|---|---|
| `100` | `.a` `.b` |
| `110` | `.a` `.b` |
| `245` | `.a` `.b` `.c` `.d` |
| `264` | `.a` `.b` `.c` |
| `490` | `.a` |
| `700` | `.a` `.b` |
| `710` | `.a` `.b` |

[↑ Back to all evaluation methods](#evaluation-methods)

### Methods: Set Comparisons

`f1-score`, `precision-score`, and `recall-score` compare sets of values from the eval and reference records for values with unambiguous equality.

The methods are intentionally restricted to values that can be compared exactly, without fuzzy matching or additional heuristics. They currently compare language codes from `041.a`, authority identifiers from `.0`, and relator codes from `.4`.

Values are treated as sets. For each comparison, values present in both eval and reference are true positives, values only present in eval are false positives, and values only present in the reference are false negatives. The selected method determines how these values are combined into a score:

``` text
precision = true positives / (true positives + false positives)
recall = true positives / (true positives + false negatives)
F1 = 2 × true positives / (2 × true positives + false positives + false negatives)
```

Only selected fields and subfields participate in a comparison. Comparisons for which both eval and reference contain no values are omitted. For `precision-score`, a comparison is also omitted when the eval contains no values, because precision is undefined. For `recall-score`, a comparison is omitted when the reference contains no values, because recall is undefined.

The method score is the mean of all applicable comparison scores.

**Requires:** gold or platinum

**Supports:**

| Field | Subfields |
|---|---|
| `041` | `.a` |
| `100` | `.0` `.4` |
| `110` | `.0` `.4` |
| `700` | `.0` `.4` |
| `710` | `.0` `.4` |

[↑ Back to all evaluation methods](#evaluation-methods)

### Method: Subfield Cardinality

`subfield-cardinality` evaluates whether the eval record contains the same amount of selected MARC data as a gold or platinum reference record.

The method operates on the subfield level, including the virtual subfields of `008`, and considers only cardinality. For example, if both records contain exactly one `245.a`, the score equals `1.0`. In general, the score is computed as the ratio between the smaller and larger count. If both counts are `0`, the score is `1.0` (subfield absence can be desired). The actual content of the values does not affect the score and can instead be evaluated using other methods. 

#### Standard fields

For fields other than `100`, `110`, `264`, `700`, and `710`, occurrences of each selected subfield are counted globally in the eval and reference records, for example:

```text
Eval:
041 $a ltz $a fre

Reference:
041 $a ltz
```

produces the following cardinality comparison for `041.a`:

```text
eval count = 2
reference count = 1
score = 0.5
```

#### Mapped fields

For person, corporate, and `264` fields, cardinality is evaluated separately within each mapped pair for every selected subfield. A mapped pair contributes even when the selected subfield is absent on both sides.

Consider the following example:

``` text
Eval:
100 $a Alice $0 X
700 $a Bob
700 $a Charlie $0 Z

Reference:
700 $a Alice $0 X
700 $a Bob $0 Y
```

Alice and Bob are mapped, while Charlie is unmatched. For `.0`, this produces:

``` text
Alice   ↔ Alice: 1 vs 1 → 1.0
Bob     ↔ Bob:   0 vs 1 → 0.0
Charlie ↔ —:     1 vs 0 → 0.0

score = (1.0 + 0.0 + 0.0) / 3 = 0.333
```

Unmatched fields are included only when they contain the selected subfield. Charlie therefore contributes to `.0` because it contains `$0 Z`. For `.d` the same records produce:

``` text
Alice ↔ Alice: 0 vs 0 → 1.0
Bob   ↔ Bob:   0 vs 0 → 1.0

score = (1.0 + 1.0) / 2 = 1.0
```

Charlie does not contribute because the unmatched field contains no `.d`. If there are no field occurrences on either side, cardinality is considered correct (`0 vs 0`) and produces a score of `1.0`.

#### Aggregation

Each selected field or subfield produces a score. For standard fields, this score is obtained directly from the global cardinality comparison. For mapped fields, the score for a selected subfield is the mean of its mapped and applicable unmatched occurrence comparisons:

```text
subfield score = sum of occurrence comparison scores / number of occurrence comparisons
```

The method score is calculated as the mean of all selected field and subfield scores.

**Requires:** gold or platinum

**Supports:**

| Field | Subfields |
|---|---|
| `008` | `.00-05` `.35-37` |
| `020` | `.a` |
| `041` | `.a` |
| `100` | `.a` `.b` `.d` `.0` `.e` `.4` |
| `110` | `.a` `.b` `.d` `.0` `.e` `.4` |
| `245` | `.a` `.b` `.c` `.d` |
| `264` | `.a` `.b` `.c` |
| `300` | `.a` `.b` |
| `490` | `.a` |
| `700` | `.a` `.b` `.d` `.0` `.e` `.4` |
| `710` | `.a` `.b` `.d` `.0` `.e` `.4` |

[↑ Back to all evaluation methods](#evaluation-methods)

### Method: Record Usability

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
- **Corporate presence (`110`, `710`)**: if the reference contains at least one corporate name in the selected fields, the eval record must also contain at least one. The number and identity of corporate names do not need to match. Subfields `.a` and `.b` are treated as parts of the same corporate name and are concatenated as `.a + .b`. If either is selected, the combined name is considered here.

Every executed criterion is listed in the diagnostic output under either `passed` or `failed`.

**Requires:** gold or platinum and an [LLM](#llm-configuration)

**Supports:**

| Field | Subfields |
|---|---|
| `020` | `.a` |
| `110` | `.a` `.b` |
| `245` | `.a` |
| `710` | `.a` `.b` |

[↑ Back to all evaluation methods](#evaluation-methods)

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
008.00-05, 008.35-37
020.a
041.a
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