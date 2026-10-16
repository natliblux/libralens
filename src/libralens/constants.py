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

TITLE_SEMANTICS_SYSTEM_PROMPT = """
Identify semantically important words or concepts that are present in one title but missing from another.

Ignore articles, prepositions, conjunctions, punctuation, capitalization, and other semantically unimportant words.

If nothing important is missing, respond exactly with:
OK

Otherwise, respond only with a comma-separated list of the missing words or concepts.
""".strip()

TITLE_SEMANTICS_USER_PROMPT = """
Title 1:
[TITLE_1]

Title 2:
[TITLE_2]
""".strip()