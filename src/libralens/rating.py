import json
from .document import Document
from pathlib import Path
from .funcs import compute_scores
from .plot import create_results_plot
from .record import Record
from .constants import HUMAN_RATINGS, FIELD_GROUPS, GROUPED_FIELDS
from .enums import InputFormat

class RatingSession:

    def __init__(self, output: Path):
        self.output = Path(output)

    def create(self, runs, n_documents: int) -> None:

        config = {
            "runs": [
                {
                    "method": run.method,
                    "fields": {field: sorted(subfields) for field, subfields in run.fields.items()}
                }
                for run in runs
            ],
            "n_documents": n_documents
        }

        ratings = {
            "documents": {
                str(i): {"completed": False, "rating": None, "fields": {}}
                for i in range(n_documents)
            }
        }

        (self.output / "session.json").write_text(json.dumps(config, indent=4, ensure_ascii=False), encoding="utf-8")
        (self.output / "ratings.json").write_text(json.dumps(ratings, indent=4, ensure_ascii=False), encoding="utf-8")

    def load_ratings(self) -> dict:

        return json.loads((self.output / "ratings.json").read_text(encoding="utf-8"))

    def build_rows(self, document: Document) -> list[dict]:

        selected = self._get_selected_fields()
        rows = self._align_eval_fields(document)
        self._align_reference_fields(document, rows)
        self._add_missing_fields(rows, selected)
        return self._prepare_rows(rows, selected)

    def save_document(self, document_id: int, rating: dict) -> bool:

        document = self._get_document(document_id)
        fields = rating.get("fields", {})
        self._validate_fields(document, fields)
        completed = self._is_complete(document, rating)
        ratings = self.load_ratings()
        previous = ratings["documents"][str(document_id)]

        if previous["completed"] and not completed:
            raise ValueError(f"cannot remove rating from completed document {document_id}")

        ratings["documents"][str(document_id)] = {
            "completed": completed,
            "rating": rating.get("rating"),
            "fields": fields
        }

        (self.output / "ratings.json").write_text(json.dumps(ratings, indent=4, ensure_ascii=False), encoding="utf-8")

        if completed:
            all_completed = all(doc["completed"] for doc in ratings["documents"].values())
            self._update_results(document_id, rating, document, all_completed)

        return completed

    def initial_document(self) -> int:

        documents = self.load_ratings()["documents"]
        for document_id, document in documents.items():
            if not document["completed"]:
                return int(document_id)
        return max(len(documents) - 1, 0)

    def _get_document(self, document_id: int) -> Document:

        config = json.loads((self.output / "session.json").read_text(encoding="utf-8"))
        n_documents = config["n_documents"]
        if document_id < 0 or document_id >= n_documents:
            raise ValueError(f"invalid document id: {document_id}")
        width = len(str(n_documents - 1))
        directory = self.output / "documents" / f"{document_id:0{width}d}"
        records = {}
        for name in ("eval", "gold", "platinum"):
            path = directory / f"{name}.xml"
            records[name] = Record(path.read_text(encoding="utf-8"), InputFormat.XML) if path.is_file() else None
        return Document(eval=records["eval"], gold=records["gold"], platinum=records["platinum"])

    def _get_selected_fields(self) -> dict:

        config = json.loads((self.output / "session.json").read_text(encoding="utf-8"))
        run = next(run for run in config["runs"] if run["method"] == "human-rating")
        selected = {tag: list(subfields) for tag, subfields in run["fields"].items()}

        for group in FIELD_GROUPS:
            if not any(tag in selected for tag in group):
                continue
            subfields = set().union(*(selected.get(tag, []) for tag in group))
            for tag in group:
                selected[tag] = sorted(subfields)

        return selected

    def _validate_fields(self, document: Document, fields: dict) -> None:

        rows = {row["id"]: row for row in self.build_rows(document)}
        eval_fields = {field["id"]: field for field in document.eval.fields}
        selected = self._get_selected_fields()
        valid_ratings = set(HUMAN_RATINGS)

        for field_id, field_rating in fields.items():

            row = rows.get(field_id)
            if row is None:
                raise ValueError(f"invalid field id: {field_id}")
            if not row["selected"]:
                raise ValueError(f"field {row['tag']} is not selected for rating")

            value = field_rating.get("rating")
            if value is not None and value not in valid_ratings:
                raise ValueError(f"invalid rating for field {field_id}: {value}")

            subfield_ratings = field_rating.get("subfields", {})
            if row["eval"] is None:
                if subfield_ratings:
                    raise ValueError(f"missing field {field_id} cannot have subfield ratings")
                continue

            field = eval_fields[row["eval"]]

            for subfield_id, subfield_rating in subfield_ratings.items():
                subfield = next((s for s in field.get("subfields", []) if str(s["id"]) == subfield_id), None)
                if subfield is None:
                    raise ValueError(f"invalid subfield id: {subfield_id}")
                if subfield["code"] not in selected.get(field["tag"], []):
                    raise ValueError(f"subfield {field['tag']}${subfield['code']} is not selected for rating")
                if subfield_rating not in valid_ratings:
                    raise ValueError(f"invalid rating for {field['tag']}${subfield['code']}: {subfield_rating}")

    def _is_complete(self, document: Document, rating: dict) -> bool:

        if rating.get("rating") not in HUMAN_RATINGS:
            return False

        selected = self._get_selected_fields()
        fields = rating.get("fields", {})
        eval_fields = {field["id"]: field for field in document.eval.fields}

        for row in self.build_rows(document):

            if not row["selected"]:
                continue
            field_rating = fields.get(row["id"], {})
            if field_rating.get("rating") not in HUMAN_RATINGS:
                return False
            if row["eval"] is None:
                continue

            field = eval_fields[row["eval"]]
            for subfield in field.get("subfields", []):
                if subfield["code"] not in selected.get(field["tag"], []):
                    continue
                value = field_rating.get("subfields", {}).get(str(subfield["id"]))
                if value not in HUMAN_RATINGS:
                    return False

        return True

    def _build_subfields(self, field: dict, ratings: dict) -> dict:

        result = {}

        for subfield in field.get("subfields", []):

            rating = ratings.get(str(subfield["id"]))
            if rating is None:
                continue

            code = subfield["code"]
            values = result.setdefault(code, [])
            occurrence = sum(s["code"] == code for s in field["subfields"][:subfield["id"]])

            while len(values) <= occurrence:
                values.append(None)

            values[occurrence] = {
                "value": subfield["value"],
                "score": HUMAN_RATINGS[rating]
            }

        return result

    def _build_info(self, document: Document, ratings: dict) -> dict:

        info = {}
        occurrences = {}
        eval_fields = {field["id"]: field for field in document.eval.fields}

        for row in self.build_rows(document):

            field_rating = ratings.get(row["id"])
            if field_rating is None:
                continue

            tag = row["tag"]
            occurrence = occurrences.get(tag, 0)
            occurrences[tag] = occurrence + 1
            values = info.setdefault(tag, [])

            while len(values) <= occurrence:
                values.append(None)
            field = eval_fields.get(row["eval"]) if row["eval"] is not None else None

            values[occurrence] = {
                "score": self._field_score(field_rating) if field_rating.get("rating") is not None else None,
                "rating": HUMAN_RATINGS[field_rating["rating"]] if field_rating.get("rating") is not None else None,
                "subfields": self._build_subfields(field, field_rating.get("subfields", {})) if field is not None else {}
            }

        return info

    def _field_score(self, field_rating: dict) -> float:

        rating = HUMAN_RATINGS[field_rating["rating"]]
        subfields = [HUMAN_RATINGS[value] for value in field_rating.get("subfields", {}).values()]

        if not subfields:
            return rating

        return (rating + sum(subfields) / len(subfields)) / 2

    def _document_score(self, rating: dict) -> float:

        document_rating = HUMAN_RATINGS[rating["rating"]]
        fields = [self._field_score(field) for field in rating.get("fields", {}).values()]

        if not fields:
            return document_rating

        return (document_rating + sum(fields) / len(fields)) / 2

    def _update_results(self, document_id: int, rating: dict, document: Document, all_completed: bool) -> None:

        path = self.output / "results.json"
        results = json.loads(path.read_text(encoding="utf-8"))

        result = next(result for result in results if result["id"] == document_id)
        result["methods"]["human-rating"] = {
            "score": self._document_score(rating),
            "rating": HUMAN_RATINGS[rating["rating"]],
            "info": self._build_info(document, rating.get("fields", {}))
        }

        config = json.loads((self.output / "session.json").read_text(encoding="utf-8"))
        methods = [run["method"] for run in config["runs"]]

        _, method_scores, overall_score = compute_scores(results, methods)

        path.write_text(json.dumps(results, indent=4, ensure_ascii=False), encoding="utf-8")

        if all_completed:
            create_results_plot(
                results=results,
                methods=[method for method in methods if method in method_scores],
                overall_score=overall_score,
                output_path=self.output / "results.png"
            )

    def _align_eval_fields(self, document: Document) -> list[dict]:

        references = {
            "gold": document.gold.fields if document.gold is not None else [],
            "platinum": document.platinum.fields if document.platinum is not None else []
        }

        mappings = {
            "gold": document.eval_to_gold_mapping,
            "platinum": document.eval_to_platinum_mapping
        }

        rows = []
        used = {"gold": set(), "platinum": set()}

        for eval_field in document.eval.fields:

            row = {"eval": eval_field, "gold": None, "platinum": None}

            for name in ("gold", "platinum"):
                mapped_id = mappings[name].get(eval_field["id"])
                reference = next((field for field in references[name] if field["id"] == mapped_id), None)

                if reference is not None:
                    row[name] = reference
                    used[name].add(reference["id"])

            rows.append(row)

        for row in rows:
            for name in ("gold", "platinum"):

                if row[name] is not None:
                    continue

                reference = next((
                    field for field in references[name]
                    if field["tag"] == row["eval"]["tag"] and field["id"] not in used[name]
                ), None)

                if reference is not None:
                    row[name] = reference
                    used[name].add(reference["id"])

        return rows

    def _align_reference_fields(self, document: Document, rows: list[dict]) -> None:

        gold_fields = document.gold.fields if document.gold is not None else []
        platinum_fields = document.platinum.fields if document.platinum is not None else []

        used_gold = {row["gold"]["id"] for row in rows if row["gold"] is not None}
        used_platinum = {row["platinum"]["id"] for row in rows if row["platinum"] is not None}

        for gold in gold_fields:

            if gold["id"] in used_gold:
                continue

            mapped_id = document.gold_to_platinum_mapping.get(gold["id"])
            platinum = next((field for field in platinum_fields if field["id"] == mapped_id), None)

            if platinum is None or platinum["id"] in used_platinum:
                platinum = next((
                    field for field in platinum_fields
                    if field["tag"] == gold["tag"] and field["id"] not in used_platinum
                ), None)

            rows.append({"eval": None, "gold": gold, "platinum": platinum})
            used_gold.add(gold["id"])

            if platinum is not None:
                used_platinum.add(platinum["id"])

        for platinum in platinum_fields:
            if platinum["id"] not in used_platinum:
                rows.append({"eval": None, "gold": None, "platinum": platinum})

    def _add_missing_fields(self, rows: list[dict], selected: dict) -> None:

        selected_tags = set(selected)
        groups = list(FIELD_GROUPS)
        groups.extend({tag} for tag in sorted(selected_tags - GROUPED_FIELDS))

        for group in groups:

            if not selected_tags & group:
                continue

            present = any(
                field is not None and field["tag"] in group
                for row in rows
                for field in (row["eval"], row["gold"], row["platinum"])
            )

            if not present:
                rows.append({
                    "eval": None,
                    "gold": None,
                    "platinum": None,
                    "placeholder": "/".join(sorted(group))
                })

    def _prepare_rows(self, rows: list[dict], selected: dict) -> list[dict]:

        selected_tags = set(selected)

        for row in rows:
            field = row["eval"] or row["gold"] or row["platinum"]
            tag = field["tag"] if field is not None else row["placeholder"]

            row["tag"] = tag
            row["selected"] = bool(set(tag.split("/")) & selected_tags)

        rows.sort(key=lambda row: int(row["tag"].split("/")[0]))

        occurrences = {}

        for row in rows:
            if row["eval"] is not None:
                row["id"] = str(row["eval"]["id"])
            else:
                tag = row["tag"]
                occurrence = occurrences.get(tag, 0)
                occurrences[tag] = occurrence + 1
                row["id"] = f"missing:{tag}:{occurrence}"

        return [
            {
                "id": row["id"],
                "tag": row["tag"],
                "selected": row["selected"],
                "eval": row["eval"]["id"] if row["eval"] is not None else None,
                "gold": row["gold"]["id"] if row["gold"] is not None else None,
                "platinum": row["platinum"]["id"] if row["platinum"] is not None else None
            }
            for row in rows
        ]