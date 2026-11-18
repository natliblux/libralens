# LibraLens

![Status](https://img.shields.io/badge/status-work_in_progress-orange)

<p align="left">
  <img src="assets/logo.png" alt="LibraLens logo" width="400">
</p>

LibraLens is a Python library for evaluating the quality of MARC 21 records. It supports records in XML and text formats, which are primarily evaluated against **gold** and **platinum** reference records:

* **Gold** represents a record based on experienced human-level cataloging.
* **Platinum** represents a maximized record version exceeding general cataloging expectations.

LibraLens provides a flexible evaluation framework combining rule-based, LLM-based, and human-driven evaluation methods. Evaluation runs can be configured to target specific MARC fields, and their results can be combined through customizable aggregation functions to assess overall dataset quality.

## Contents

- [Installation](#installation)
- [Concepts](#concepts)
  - [Dataset](#dataset)
  - [Documents](#documents)
  - [Methods](#methods)
  - [Fields](#fields)
  - [Grouping](#grouping)
  - [Mapping](#mapping)
  - [Runs](#runs)
- [Usage](#usage)
  - [Run Methods](#run-methods)
  - [Aggregate](#aggregate)
- [Evaluation Methods](#evaluation-methods)
  - [Field Validity](#method-field-validity)
  - [Text Match](#method-text-match)
  - [Entity Coverage](#method-entity-coverage)
  - [Semantic Recall](#method-semantic-recall)
  - [Common Substring](#methods-fuzzy-comparisons)
  - [Edit Distance](#methods-fuzzy-comparisons)
  - [Exact Match](#method-exact-match)
  - [F1 Score](#methods-set-comparisons)
  - [Precision Score](#methods-set-comparisons)
  - [Recall Score](#methods-set-comparisons)
  - [Subfield Cardinality](#method-subfield-cardinality)
  - [Subfield Presence](#method-subfield-presence)
  - [Human Rating](#method-human-rating)
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

Install LibraLens from the project directory, required Python dependencies are installed automatically:

```bash
pip install .
```

For a quick start, before diving deeper into the LibraLens documentation, you can evaluate MARC records against a gold standard by providing the paths to the corresponding XML files:

```bash
libralens --eval [path-to-xml-file] --gold [path-to-gold-xml]
```

## Concepts

### Dataset

LibraLens lets you evaluate the quality of a **dataset**, which consists of **documents**.

### Documents

A document consists of:
- an **eval** record to be evaluated (mandatory)
- an optional **gold** reference record
- an optional **platinum** reference record
- the optional source **PDF**
- the optional plain **text** from the source PDF

MARC records can be provided as `.xml` or `.txt` files, either individually or in directories. XML files may contain multiple records, while PDF and text files each correspond to a single document. Source text can be provided directly as a `.txt` file or automatically extracted from a PDF by LibraLens.

Individual document components are matched as described in [Document Matching](#document-matching).

The selected evaluation **methods** determine which components are required. For example, `text-match` requires source text, while comparison-based methods such as `edit-distance` require a gold and/or platinum reference record.

### Methods

LibraLens provides various evaluation methods that produce normalized scores between `0.0` and `1.0` (`None` if not applicable). Each method supports a defined set of MARC fields and subfields. See [Evaluation Methods](#evaluation-methods) for the complete list.

### Fields

LibraLens supports a defined set of MARC fields, subfields, and indicators, listed [here](#marc-scope). Complete fields are selected by their MARC tag (e.g. `245`), while individual subfields are selected using dot notation (e.g. `700.a`). For controlfield `008`, positions `00-05` and `35-37` are treated as virtual subfields. Indicators are handled similarly (`ind1` and `ind2`). Both can be selected using dot notation (e.g. `008.35-37`, `245.ind1`). Selecting a complete field includes all its supported subfields and indicators. For **grouped** fields, selecting a subfield also includes the corresponding subfield across the group (e.g. `700.a` also selects `100.a`).

### Grouping

The person fields `100/700` and the corporate fields `110/710` are each treated as one **group**, which allows related information to be evaluated together. For example, person names in `100` and `700` are treated as belonging to the same group, rather than as two separate categories.

### Mapping

For certain methods, LibraLens **maps** corresponding field occurrences between eval and reference records. Mapping applies to person (`100/700`), corporate (`110/710`), and `264` fields. Person and corporate mappings may cross MARC tags within their respective groups, while 264 occurrences are mapped only to other 264 occurrences.

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

Mapping allows evaluation methods to compare corresponding occurrences regardless of their order or, for grouped fields, their MARC tags, while accounting for unmatched occurrences.

### Runs

An evaluation **run** applies one method to a selection of MARC fields and subfields. Two ways of configuring runs are supported:

- **Global selection:** Select methods and optionally specify fields/subfields. If no methods are specified, all methods whose requirements are satisfied by the provided document components are automatically selected. Each method runs on its supported fields/subfields, restricted to the selected fields if provided.
- **Targeted runs:** Define runs with their own method, optional identifier, and fields/subfields. This allows targeted evaluations instead of applying every method to every supported field. If no identifier is provided, the method name is used.

If no fields are specified, all fields supported by the method are considered.

Using the CLI:

```bash
# Global selection
libralens --eval records.xml --gold records.xml --methods edit-distance exact-match --fields 245 100.a

# Targeted runs defined in JSON
libralens --eval records.xml --gold records.xml --runs runs.json
```

Using Python:

```python
from libralens import LibraLens, Run

# Global selection
LibraLens(eval="records.xml", gold="records.xml", methods=["edit-distance", "exact-match"], fields=["245", "100.a"])

# Targeted runs
LibraLens(eval="records.xml", gold="records.xml", runs=[
    Run(id="titles", method="edit-distance", fields=["245"]),
    Run(id="authors", method="exact-match", fields=["100.a"])
])
```

## Usage

LibraLens can be used through the command-line interface (CLI) or as a Python library. Both follow a two-step workflow:

- **Run** evaluation methods to produce document-level results.
- **Aggregate** the resulting scores into custom dataset-level quality metrics.

The main commands are:

| Action | CLI | Python |
|---|---|---|
| Run evaluation methods | `libralens run` (or simply `libralens`) | `LibraLens.run()` |
| Aggregate scores | `libralens aggregate` | `LibraLens.aggregate()` |
| Resume human rating | `libralens rate` | `LibraLens.rate()` |

### Run Methods

At minimum, LibraLens requires **eval** records. Additional document components, such as gold/platinum reference records, source PDFs, or plain text, enable methods that depend on them. See [Evaluation Methods](#evaluation-methods) for each method's requirements. If no methods are specified, LibraLens automatically selects those whose requirements are satisfied by the provided components.

All CLI options for `run`:

| Option | Description |
|---|---|
| `--eval` | Provides eval records |
| `--methods` | Selects evaluation methods |
| `--runs` | Provides a JSON file defining targeted runs |
| `--fields` | Selects MARC fields and subfields |
| `--gold` | Provides gold reference records |
| `--platinum` | Provides platinum reference records |
| `--text` | Provides source plain text |
| `--pdf` | Provides source PDF files |
| `--output` | Defines the output directory |

The `run` subcommand can be omitted. Run `libralens --help` for the complete command-line reference.

Alternatively, using Python:

```python
from libralens import LibraLens

ll = LibraLens(
    eval="records/",
    gold="gold/",
    platinum="platinum/",
    text="text/",
    pdf="pdf/",
    methods=["edit-distance", "exact-match"],
    fields=["245", "100.a"],
    output="output/",
    verbose=True
)

results = ll.run()
```

For more targeted evaluations, configure individual [runs](#runs) (use `runs` parameter with a file path instead of `methods` and `fields`). Example `runs.json`:

```json
[
    {"id": "titles", "method": "edit-distance", "fields": ["245.a", "245.b"]},
    {"id": "authors", "method": "exact-match", "fields": ["100.a"]}
]
```

#### Human Rating

When a run includes the `human-rating` method, ratings are collected through a **web-based interface** rather than calculated automatically. To reopen the interface and continue rating:

```bash
libralens rate output/
```

```python
LibraLens.rate("output/")
```

#### Results

When an output directory is provided, LibraLens writes `results.json` with detailed evaluation results and unweighted scores. Each document has an overall score calculated as the mean of its applicable run scores. Each run stores its `method`, `score`, standardized `references` scores (explained under [Aggregate](#aggregate)), and an `info` dictionary containing method-specific diagnostics.

```json
[
    {
        "id": 0,
        "score": 0.8,
        "runs": {
            "titles": {
                "method": "edit-distance",
                "score": 0.8,
                "references": {},
                "info": {}
            }
        }
    }
]
```

Scores range from `0.0` to `1.0` (higher is better), or may be `None` when not applicable. Document and run averages are also available in Python as `ll.document_scores` and `ll.run_scores`.

### Aggregate

While `info` is method-specific, the `references` structure in `results.json` exposes scores in a standardized hierarchy for each applicable reference: `gold`, `platinum`, or `none`. Scores can be available at the **run**, **field/group**, and **subfield/indicator** levels. Methods that do not compare against reference records store their scores under `none`.

Aggregation uses these standardized scores to calculate custom dataset-level quality metrics.

#### Scores

Running `aggregate` also generates `scores.json`, organizing the scores from `results.json` by flattened keys. Keys follow the pattern:

```text
[run-identifier].[reference].[field].[subfield]
```

Shorter keys represent higher levels, such as `titles`, `titles.gold`, or `titles.gold.245`. Each key in `scores.json` contains the available scores by document ID and their `average` across documents.

To list the available keys and **the number of documents with a score for each key**, use:

```bash
libralens aggregate output/ --keys
```

```python
LibraLens.aggregate("output/", keys=True)
```

#### Custom Function

MARC record quality is not necessarily defined the same way by every institution. Some fields and subfields matter more than others, and different evaluation methods may be better suited to different types of information. Custom aggregation functions let you reflect these priorities when combining scores into quality metrics.

Create a Python module under `libralens/aggregate/` with an `aggregate` function. It receives the flattened scores for **one document** and returns a dictionary of named metrics; unavailable scores are represented by `None`:

```python
def aggregate(scores: dict) -> dict[str, float | None]:
    ...
```

The included `dummy` module illustrates this approach by averaging all available scores without weighting them. Run an aggregation module by name:

```bash
libralens aggregate output/ dummy
```

```python
averages = LibraLens.aggregate("output/", "dummy", verbose=True)
```

LibraLens applies the function to each document, then averages each named metric across documents with available values to produce dataset-level metrics.

## Evaluation Methods

LibraLens currently provides 13 evaluation methods:

| Method | Requires | Purpose |
|---|---|---|
| [`field-validity`](#method-field-validity) |  | Checks whether the eval record conforms to known formats and controlled vocabularies. |
| [`text-match`](#method-text-match) | Plain Text | Matches strings from the eval record with the underlying PDF plain text. |
| [`entity-coverage`](#method-entity-coverage) | [LLM](#llm-configuration) | Measures how well the name fields cover entities mentioned in the statement of responsibility. |
| [`semantic-recall`](#method-semantic-recall) | Reference and [LLM](#llm-configuration) | Compares the eval record to the reference record using recall for semantically relevant words. |
| [`common-substring`](#methods-fuzzy-comparisons) | Reference | Compares the eval record to the reference record using the longest common substring. |
| [`edit-distance`](#methods-fuzzy-comparisons) | Reference | Compares the eval record to the reference record using edit distance. |
| [`exact-match`](#method-exact-match) | Reference | Compares the eval record to the reference record using exact equality. |
| [`f1-score`](#methods-set-comparisons) | Reference | Computes the F1 score between the eval and reference record for values with unambiguous equality. |
| [`precision-score`](#methods-set-comparisons) | Reference | Computes the precision score between the eval and reference record for values with unambiguous equality. |
| [`recall-score`](#methods-set-comparisons) | Reference | Computes the recall score between the eval and reference record for values with unambiguous equality. |
| [`subfield-cardinality`](#method-subfield-cardinality) | Reference | Compares the cardinality of selected fields and subfields in the eval and reference records. |
| [`subfield-presence`](#method-subfield-presence) | Reference | Compares the presence of subfields in eval and reference records. |
| [`human-rating`](#method-human-rating) | PDF and Output | Provides a web interface for humans to rate the eval record. |

Methods requiring a reference can use gold, platinum, or both. When both are supplied, comparisons are performed independently against each reference and the run score is an average.

### Method: Field Validity

`field-validity` checks whether the eval record conforms to known formats and controlled vocabularies.

The currently implemented checks are:

- `008.00-05`: a valid six-digit date
- `008.35-37`: a valid language code
- `020.a`: a valid ISBN-10 or ISBN-13, including its checksum
- `041.a`: valid language codes
- `.4` in person and corporate name fields: valid relator codes

Each checked value is classified as valid or invalid:

```text
method score = valid checks / all checks
```

**Requires:** no additional document components

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

`text-match` matches strings from the eval record against the source document's plain text.

Before matching, both MARC values and source text undergo Unicode NFKC normalization, lowercasing, and whitespace normalization. Some MARC values generate alternative representations:

- `020.a`: original ISBN, a compact version without spaces or hyphens, and a version with spaces instead of hyphens
- `100/700`: `.a` and `.b` combined into a person name, with variants for ordering and punctuation
- `110/710`: `.a` and `.b` combined into a corporate name
- `245`: title, subtitle, and statement of responsibility matched separately
- `264`: places, publishers, and dates matched separately
- `490.a`: matched separately

A logical value counts as matched if **any** generated variant appears in the text. For example, `Doe John`, `Doe, John`, `John Doe`, and `John, Doe` represent one logical person-name value.

```text
method score = matched values / all checked values
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

### Method: Entity Coverage

`entity-coverage` measures how well the name fields represent persons and corporate bodies mentioned in the statement of responsibility (`245.c`). An LLM identifies distinct entities in that statement and compares them with names from `100/700` and `110/710`. Subfields `.a` and `.b` are considered together when comparing names, allowing variations in punctuation, abbreviations, initials, spelling, and ordering.

```text
method score = matched entities / identified entities in 245.c
```

Each identified entity contributes equally. Extra entities in the name fields do not reduce the score. If no relevant entities are identified, the score is `None`.

**Requires:** [LLM](#llm-configuration)

**Supports:**

| Field | Subfields |
|---|---|
| `100` | `.a` |
| `110` | `.a` |
| `700` | `.a` |
| `710` | `.a` |

[↑ Back to all evaluation methods](#evaluation-methods)

### Method: Semantic Recall

`semantic-recall` uses an LLM to check whether the eval record preserves the **important words and concepts** from a gold or platinum reference. Synonyms and equivalent expressions count as matches; differences in articles, prepositions, punctuation, capitalization, and other unimportant wording are ignored.

This is a **directional, binary** comparison: extra information in the eval record is not penalized. Unlike the fuzzy comparison methods below, it does not award partial similarity scores for individual comparisons.

```text
1.0 = no important reference concepts are missing
0.0 = at least one important reference concept is missing
```

The method score combines applicable comparisons; missing or unmatched values are not automatically treated as zero-score string comparisons.

**Requires:** gold or platinum and an [LLM](#llm-configuration)

**Supports:**

| Field | Subfields |
|---|---|
| `110` | `.a` `.b` |
| `245` | `.a` `.b` `.d` |
| `264` | `.a` `.b` `.c` |
| `490` | `.a` |
| `710` | `.a` `.b` |

[↑ Back to all evaluation methods](#evaluation-methods)

### Methods: Fuzzy Comparisons

`common-substring` and `edit-distance` compare corresponding strings in the eval and gold or platinum records. Each comparison returns a normalized score between `0.0` and `1.0`:

- `common-substring` measures similarity using the longest continuous substring shared by both values.
- `edit-distance` uses normalized Levenshtein similarity.

Only values for which a comparison can be established contribute to the score. Missing, extra, or otherwise unmatched values are omitted rather than scored as `0.0`. These methods measure similarity, not completeness or cardinality; use [`subfield-cardinality`](#method-subfield-cardinality) for the latter.

For person and corporate names, `.a` and `.b` are combined before comparison (for example, `710 $a Example Organization $b Research Department` becomes `Example Organization Research Department`). In `245`, selected subfields are compared individually; when both `.a` and `.b` are selected, their combined title is also compared. `490.a` is compared individually. In `264`, `.a`, `.b`, and `.c` are compared within corresponding mapped occurrences.

```text
method score = sum of applicable comparison scores / number of applicable comparisons
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

### Method: Exact Match

`exact-match` compares corresponding individual subfield values and indicators using strict string equality, without normalization. Differences in capitalization, whitespace, or punctuation result in a score of `0.0`. Unlike the fuzzy methods, it does not concatenate subfields.

Only values for which a comparison can be established contribute; missing, extra, or unmatched values are omitted rather than assigned `0.0`.

```text
method score = sum of applicable comparison scores / number of applicable comparisons
```

**Requires:** gold or platinum

**Supports:**

| Field | Subfields |
|---|---|
| `008` | `.00-05` `.35-37` |
| `020` | `.ind1` `.ind2` `.a` |
| `041` | `.ind1` `.ind2` |
| `100` | `.ind1` `.ind2` `.d` `.0` `.e` `.4` |
| `110` | `.ind1` `.ind2` `.d` `.0` `.e` `.4` |
| `245` | `.ind1` `.ind2` |
| `264` | `.ind1` `.ind2` `.c` |
| `300` | `.ind1` `.ind2` `.a` `.b` |
| `490` | `.ind1` `.ind2` |
| `700` | `.ind1` `.ind2` `.d` `.0` `.e` `.4` |
| `710` | `.ind1` `.ind2` `.d` `.0` `.e` `.4` |

[↑ Back to all evaluation methods](#evaluation-methods)

### Methods: Set Comparisons

`f1-score`, `precision-score`, and `recall-score` compare sets of values from eval and reference records when equality can be determined unambiguously. They currently cover language codes in `041.a`, authority identifiers in `.0`, and relator codes in `.4`.

Values found in both records are **true positives** (TP); values only in eval are **false positives** (FP); and values only in the reference are **false negatives** (FN).

```text
precision = TP / (TP + FP)
recall    = TP / (TP + FN)
F1        = 2 × TP / (2 × TP + FP + FN)
```

Only selected fields and subfields participate. Comparisons with no values on either side are omitted. Precision is omitted when eval has no values, and recall is omitted when the reference has no values, because the respective denominator is zero. The method score is the mean of applicable comparisons.

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

`subfield-cardinality` checks whether the eval and reference records contain the same **number** of selected subfield occurrences, including virtual `008` subfields. Content is not compared.

For each count comparison, the score is the smaller count divided by the larger. Two zero counts score `1.0` because absence on both sides agrees.

#### Standard fields

For fields other than `100`, `110`, `264`, `700`, and `710`, selected subfields are counted across the entire record:

```text
Eval:      041 $a ltz $a fre
Reference: 041 $a ltz

041.a: 2 vs 1 → 0.5
```

#### Mapped fields

For person, corporate, and `264` fields, counts are compared within mapped occurrence pairs. Mapped pairs contribute even when the selected subfield is absent on both sides. Unmatched occurrences contribute only if they contain the selected subfield.

```text
Eval:
100 $a Alice $0 X
700 $a Bob
700 $a Charlie $0 Z

Reference:
700 $a Alice $0 X
700 $a Bob $0 Y

For .0:
Alice   ↔ Alice: 1 vs 1 → 1.0
Bob     ↔ Bob:   0 vs 1 → 0.0
Charlie ↔ —:     1 vs 0 → 0.0

score = (1.0 + 0.0 + 0.0) / 3 = 0.333
```

For `.d`, Alice and Bob each score `1.0` (`0 vs 0`), while unmatched Charlie is ignored because it has no `.d`. If neither record has occurrences of a selected field, its cardinality is considered correct.

#### Aggregation

Each selected field or subfield produces a score. For mapped fields, the subfield score is the mean across applicable mapped and unmatched occurrences; the method score is the mean across selected field/subfield scores.

```text
subfield score = sum of occurrence comparison scores / number of occurrence comparisons
```

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

### Method: Subfield Presence

`subfield-presence` checks whether each selected subfield present in a gold or platinum reference is also present in the eval record. It measures **presence, not the number or content of values**.

For each applicable comparison:

```text
1.0 = the reference subfield is absent, or it is also present in eval
0.0 = the reference subfield is present but missing in eval
```

Person (`100/700`) and corporate (`110/710`) fields are treated as groups, so corresponding subfields can be found across either tag within a group. Extra subfields in eval are not penalized. The method score is the mean of applicable presence comparisons.

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


### Method: Human Rating

Unlike automated methods, `human-rating` uses a **web-based interface** to assess MARC records manually. The eval record is displayed alongside images of the source PDF. Optional gold and platinum references can also be displayed; mapped reference occurrences are aligned with the eval record.

Ratings are provided at three levels:

- **Document:** overall assessment of the eval record
- **Field:** assessment of each selected field occurrence
- **Subfield:** assessment of each selected subfield occurrence

All applicable ratings are required to complete a document. Ratings are converted into scores:

| Rating | Score |
|---|---|
| Excellent | `1.0` |
| Good | `0.66` |
| OK | `0.33` |
| Bad | `0.0` |

#### Aggregation

A field occurrence combines its direct rating with the mean of its subfield ratings. If no subfields are rated, its score equals its direct rating. The document score similarly combines the document rating with the mean of rated field scores:

```text
field score    = (field rating + mean of subfield ratings) / 2
document score = (document rating + mean of field scores) / 2
```

Repeated field occurrences contribute independently and equally. The resulting document score contributes as a run score alongside automated methods.

#### Rating Sessions

When a run includes `human-rating`, LibraLens can open the browser-based interface after automated evaluation. An output directory and source PDFs are required; reference records are optional. Only one `human-rating` run can be configured per evaluation.

```bash
libralens run --eval records/ --pdf pdf/ --output output/ --methods human-rating
```

Resume an existing rating session without rerunning evaluation:

```bash
libralens rate output/
```

Completed ratings are saved in the output directory and incorporated into `results.json` under the configured run identifier. Dataset-level quality metrics are calculated separately through [aggregation](#aggregate).

**Requires:** source PDF and output directory

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


## Configuration

### Document Matching

When individual files are provided explicitly for different document components (e.g. eval and gold), their filenames do not necessarily need to match. The files are always considered to belong to the same document. When directories are provided, corresponding eval, gold, platinum, pdf and plain-text data is matched through base filenames. For example:

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
pdf/
    record0.pdf
    record1.pdf
text/
    record0.txt
    record1.pdf
```
PDF and plain text files use the same base filename as the corresponding record. Plain text files use either the `.txt` (text is read directly) or the `.pdf` (LibraLens PDF text extraction) extension. When corresponding `.xml` files contain multiple records, eval, gold, and platinum records are paired based on their order within the file. 

> **Caution:** Record order must be consistent across corresponding eval, gold and platinum files. LibraLens does not verify that records at the same position represent the same bibliographic document. Incorrect ordering could therefore cause records to be evaluated against the wrong gold or platinum reference.

For a multi-record `.xml` file, the corresponding pdf files and plain texts are provided through a directory with the same base filename:

```
eval/
    records.xml
gold/
    records.xml
platinum/
    records.xml
pdf/
    records/
        00.pdf
        01.pdf
text/
    records/
        00.txt
        01.pdf
```
The numbered pdf and plain text files correspond to the records by their order within the `.xml` file, starting at `0`. Leading zeros are optional and do not affect matching. The number of files must match the number of records.

### LLM Configuration

Some evaluation methods require access to an LLM. LibraLens supports endpoints exposing an OpenAI-compatible Chat Completions API. The connection is configured using three environment variables:

| Variable | Required | Description |
|---|---|---|
| `LIBRALENS_LLM_URL` | yes | Base URL |
| `LIBRALENS_LLM_MODEL` | yes | Model Identifier |
| `LIBRALENS_LLM_KEY` | no | API Key |
| `LIBRALENS_LLM_RPM` | no | Maximum requests per minute (default: 0, unlimited) |
| `LIBRALENS_LLM_RETRIES` | no | Maximum retry attempts for failed requests (default: 3) |

For example:
```bash
export LIBRALENS_LLM_URL="https://api.openai.com/v1"
export LIBRALENS_LLM_MODEL="gpt-6"
export LIBRALENS_LLM_KEY="example-key"
export LIBRALENS_LLM_RPM=300
export LIBRALENS_LLM_RETRIES=3
```

The API key can be omitted depending on the endpoint (e.g. locally hosted models).

Rate limiting spaces requests over time to avoid exceeding provider limits. When disabled, requests are sent without an additional delay. Failed requests caused by rate limits or temporary server errors are automatically retried with exponential backoff. Both settings can be adjusted to accommodate different LLM providers and their usage limits.

### MARC Scope

Aggregating all methods, LibraLens currently supports the following MARC 21 fields, subfields and indicators:


| Field | Subfield(s) | Supported methods |
|---|---|---|
| `008` | `.00-05` `.35-37` | [`field-validity`](#method-field-validity) [`exact-match`](#method-exact-match) [`subfield-cardinality`](#method-subfield-cardinality) [`subfield-presence`](#method-subfield-presence) [`human-rating`](#method-human-rating) |
| `020` | `.ind1` `.ind2` | [`exact-match`](#method-exact-match) |
| `020` | `.a` | [`field-validity`](#method-field-validity) [`text-match`](#method-text-match) [`exact-match`](#method-exact-match) [`subfield-cardinality`](#method-subfield-cardinality) [`subfield-presence`](#method-subfield-presence) [`human-rating`](#method-human-rating) |
| `041` | `.ind1` `.ind2` | [`exact-match`](#method-exact-match) |
| `041` | `.a` | [`field-validity`](#method-field-validity) [`f1-score`](#methods-set-comparisons) [`precision-score`](#methods-set-comparisons) [`recall-score`](#methods-set-comparisons) [`subfield-cardinality`](#method-subfield-cardinality) [`subfield-presence`](#method-subfield-presence) [`human-rating`](#method-human-rating) |
| `100` `700` | `.ind1` `.ind2` | [`exact-match`](#method-exact-match) |
| `100` `700` | `.a` | [`text-match`](#method-text-match) [`entity-coverage`](#method-entity-coverage) [`common-substring`](#methods-fuzzy-comparisons) [`edit-distance`](#methods-fuzzy-comparisons) [`subfield-cardinality`](#method-subfield-cardinality) [`subfield-presence`](#method-subfield-presence) [`human-rating`](#method-human-rating) |
| `100` `700` | `.b` | [`text-match`](#method-text-match) [`common-substring`](#methods-fuzzy-comparisons) [`edit-distance`](#methods-fuzzy-comparisons) [`subfield-cardinality`](#method-subfield-cardinality) [`subfield-presence`](#method-subfield-presence) [`human-rating`](#method-human-rating) |
| `100` `700` | `.d` `.e` | [`exact-match`](#method-exact-match) [`subfield-cardinality`](#method-subfield-cardinality) [`subfield-presence`](#method-subfield-presence) [`human-rating`](#method-human-rating) |
| `100` `700` | `.0` | [`exact-match`](#method-exact-match) [`f1-score`](#methods-set-comparisons) [`precision-score`](#methods-set-comparisons) [`recall-score`](#methods-set-comparisons) [`subfield-cardinality`](#method-subfield-cardinality) [`subfield-presence`](#method-subfield-presence) [`human-rating`](#method-human-rating) |
| `100` `700` | `.4` | [`field-validity`](#method-field-validity) [`exact-match`](#method-exact-match) [`f1-score`](#methods-set-comparisons) [`precision-score`](#methods-set-comparisons) [`recall-score`](#methods-set-comparisons) [`subfield-cardinality`](#method-subfield-cardinality) [`subfield-presence`](#method-subfield-presence) [`human-rating`](#method-human-rating) |
| `110` `710` | `.ind1` `.ind2` | [`exact-match`](#method-exact-match) |
| `110` `710` | `.a` | [`text-match`](#method-text-match) [`entity-coverage`](#method-entity-coverage) [`semantic-recall`](#method-semantic-recall) [`common-substring`](#methods-fuzzy-comparisons) [`edit-distance`](#methods-fuzzy-comparisons) [`subfield-cardinality`](#method-subfield-cardinality) [`subfield-presence`](#method-subfield-presence) [`human-rating`](#method-human-rating) |
| `110` `710` | `.b` | [`text-match`](#method-text-match) [`semantic-recall`](#method-semantic-recall) [`common-substring`](#methods-fuzzy-comparisons) [`edit-distance`](#methods-fuzzy-comparisons) [`subfield-cardinality`](#method-subfield-cardinality) [`subfield-presence`](#method-subfield-presence) [`human-rating`](#method-human-rating) |
| `110` `710` | `.d` `.e` | [`exact-match`](#method-exact-match) [`subfield-cardinality`](#method-subfield-cardinality) [`subfield-presence`](#method-subfield-presence) [`human-rating`](#method-human-rating) |
| `110` `710` | `.0` | [`exact-match`](#method-exact-match) [`f1-score`](#methods-set-comparisons) [`precision-score`](#methods-set-comparisons) [`recall-score`](#methods-set-comparisons) [`subfield-cardinality`](#method-subfield-cardinality) [`subfield-presence`](#method-subfield-presence) [`human-rating`](#method-human-rating) |
| `110` `710` | `.4` | [`field-validity`](#method-field-validity) [`exact-match`](#method-exact-match) [`f1-score`](#methods-set-comparisons) [`precision-score`](#methods-set-comparisons) [`recall-score`](#methods-set-comparisons) [`subfield-cardinality`](#method-subfield-cardinality) [`subfield-presence`](#method-subfield-presence) [`human-rating`](#method-human-rating) |
| `245` | `.ind1` `.ind2` | [`exact-match`](#method-exact-match) |
| `245` | `.a` | [`text-match`](#method-text-match) [`semantic-recall`](#method-semantic-recall) [`common-substring`](#methods-fuzzy-comparisons) [`edit-distance`](#methods-fuzzy-comparisons) [`subfield-cardinality`](#method-subfield-cardinality) [`subfield-presence`](#method-subfield-presence) [`human-rating`](#method-human-rating) |
| `245` | `.b` `.d` | [`text-match`](#method-text-match) [`semantic-recall`](#method-semantic-recall) [`common-substring`](#methods-fuzzy-comparisons) [`edit-distance`](#methods-fuzzy-comparisons) [`subfield-cardinality`](#method-subfield-cardinality) [`subfield-presence`](#method-subfield-presence) [`human-rating`](#method-human-rating) |
| `245` | `.c` | [`common-substring`](#methods-fuzzy-comparisons) [`edit-distance`](#methods-fuzzy-comparisons) [`subfield-cardinality`](#method-subfield-cardinality) [`subfield-presence`](#method-subfield-presence) [`human-rating`](#method-human-rating) |
| `264` | `.ind1` `.ind2` | [`exact-match`](#method-exact-match) |
| `264` | `.a` | [`text-match`](#method-text-match) [`semantic-recall`](#method-semantic-recall) [`common-substring`](#methods-fuzzy-comparisons) [`edit-distance`](#methods-fuzzy-comparisons) [`subfield-cardinality`](#method-subfield-cardinality) [`subfield-presence`](#method-subfield-presence) [`human-rating`](#method-human-rating) |
| `264` | `.b` | [`text-match`](#method-text-match) [`semantic-recall`](#method-semantic-recall) [`common-substring`](#methods-fuzzy-comparisons) [`edit-distance`](#methods-fuzzy-comparisons) [`subfield-cardinality`](#method-subfield-cardinality) [`subfield-presence`](#method-subfield-presence) [`human-rating`](#method-human-rating) |
| `264` | `.c` | [`text-match`](#method-text-match) [`semantic-recall`](#method-semantic-recall) [`common-substring`](#methods-fuzzy-comparisons) [`edit-distance`](#methods-fuzzy-comparisons) [`exact-match`](#method-exact-match) [`subfield-cardinality`](#method-subfield-cardinality) [`subfield-presence`](#method-subfield-presence) [`human-rating`](#method-human-rating) |
| `300` | `.ind1` `.ind2` | [`exact-match`](#method-exact-match) |
| `300` | `.a` `.b` | [`exact-match`](#method-exact-match) [`subfield-cardinality`](#method-subfield-cardinality) [`subfield-presence`](#method-subfield-presence) [`human-rating`](#method-human-rating) |
| `490` | `.ind1` `.ind2` | [`exact-match`](#method-exact-match) |
| `490` | `.a` | [`text-match`](#method-text-match) [`semantic-recall`](#method-semantic-recall) [`common-substring`](#methods-fuzzy-comparisons) [`edit-distance`](#methods-fuzzy-comparisons) [`subfield-cardinality`](#method-subfield-cardinality) [`subfield-presence`](#method-subfield-presence) [`human-rating`](#method-human-rating) |


This set also defines which data is written to disk when using the `--output` option.