from importlib.resources import files
import json

def load_codes(filename: str) -> set[str]:
    path = files("libralens.data").joinpath(filename)
    with path.open("r", encoding="utf-8") as file:
        return set(json.load(file))

RELEVANT_FIELDS = {
    "008": ("00-05", "35-37"),
    "020": ("a",),
    "041": ("a",),
    "100": ("a", "b", "d", "0", "e", "4"),
    "110": ("a", "b", "d", "0", "e", "4"),
    "245": ("a", "b", "c", "d"),
    "264": ("a", "b", "c"),
    "300": ("a", "b"),
    "490": ("a",),
    "700": ("a", "b", "d", "0", "e", "4"),
    "710": ("a", "b", "d", "0", "e", "4"),
}

FIELD_GROUPS = [
    {"100", "700"},
    {"110", "710"},
]
MAPPING_GROUPS = FIELD_GROUPS + [{"264"}]
GROUPED_FIELDS = set().union(*FIELD_GROUPS)
MAPPED_FIELDS = set().union(*MAPPING_GROUPS)

MAPPING_264_IND_WEIGHT = 0.5
MAPPING_NAMES_IND_WEIGHT = 0.0

LLM_URL_ENV = "LIBRALENS_LLM_URL"
LLM_MODEL_ENV = "LIBRALENS_LLM_MODEL"
LLM_KEY_ENV = "LIBRALENS_LLM_KEY"

HUMAN_RATING_PORT = 8765

PDF_N_PAGES = 7
PDF_LARGE_IMG_DIM = 1000
PDF_IMAGE_SCALE = 3

HUMAN_RATINGS = {
    "excellent": 1.0,
    "good": 2 / 3,
    "ok": 1 / 3,
    "bad": 0.0
}

MARC_LANGUAGE_CODES = load_codes("language_codes.json")
MARC_RELATOR_CODES = load_codes("relator_codes.json")

PLOT_RESOLUTION = 10

SEMANTIC_RECALL_SYSTEM_PROMPT = """
Identify important words or concepts from Text A that are missing from Text B.
Ignore articles, prepositions, conjunctions, punctuation, capitalization, and other unimportant words.
Consider synonyms and equivalent expressions as matches.
If nothing important is missing, respond exactly with:
OK
Otherwise, respond only with a comma-separated list of missing words or concepts.
""".strip()

SEMANTIC_RECALL_USER_PROMPT = """
Text A:
[REFERENCE]

Text B:
[EVAL]
""".strip()

ENTITY_COVERAGE_SYSTEM_PROMPT = """
Identify all distinct entities of the requested type (person or corporate) mentioned in the provided statement of responsibility.
For each identified entity, preserve its name exactly as it appears in the statement of responsibility, regardless of how it is represented in the provided list.
For each identified entity, determine whether it matches an entity in the provided list.
Consider variations in name ordering, particularly inverted first and last names (e.g., "Smith, John" and "John Smith"), as well as differences in punctuation, abbreviations, initials, and spelling.
Do not invent entities or assume equivalence without sufficient evidence.
Ignore entities in the provided list that are not mentioned in the statement.

Return only a valid JSON array. Do not include Markdown formatting, code fences, or explanations.
[
    {"name": "Example Entity", "matched": true},
    {"name": "Another Entity", "matched": false}
]

Return an empty array if no entities of the requested type are identified.
""".strip()

ENTITY_COVERAGE_USER_PROMPT = """
Entity type: [ENTITY_TYPE]

Statement of responsibility:
[STATEMENT]

Entities to match against:
[ENTITIES]
""".strip()