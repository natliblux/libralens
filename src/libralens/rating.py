import json
from pathlib import Path
from .funcs import compute_scores
from .plot import create_results_plot
from .record import Record
from .constants import HUMAN_RATINGS
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

    def _get_record(self, document_id: int) -> Record:

        config = json.loads((self.output / "session.json").read_text(encoding="utf-8"))
        n_documents = config["n_documents"]

        if document_id < 0 or document_id >= n_documents:
            raise ValueError(f"invalid document id: {document_id}")

        width = len(str(n_documents - 1))
        path = self.output / "documents" / f"{document_id:0{width}d}" / "eval.xml"

        return Record(path.read_text(encoding="utf-8"), InputFormat.XML)

    def _get_selected_fields(self) -> dict:

        config = json.loads((self.output / "session.json").read_text(encoding="utf-8"))
        run = next(run for run in config["runs"] if run["method"] == "human-rating")

        return run["fields"]

    def _validate_fields(self, record: Record, fields: dict) -> None:

        selected = self._get_selected_fields()
        valid_ratings = set(HUMAN_RATINGS)

        for field_id, field_rating in fields.items():

            field = next((f for f in record.fields if f["id"] == int(field_id)), None)
            if field is None:
                raise ValueError(f"invalid field id: {field_id}")
            if field["tag"] not in selected:
                raise ValueError(f"field {field['tag']} is not selected for rating")

            rating = field_rating.get("rating")
            if rating is not None and rating not in valid_ratings:
                raise ValueError(f"invalid rating for field {field_id}: {rating}")

            for subfield_id, subfield_rating in field_rating.get("subfields", {}).items():

                subfield = next((s for s in field.get("subfields", []) if s["id"] == int(subfield_id)), None)
                if subfield is None:
                    raise ValueError(f"invalid subfield id: {subfield_id}")
                if subfield["code"] not in selected[field["tag"]]:
                    raise ValueError(f"subfield {field['tag']}${subfield['code']} is not selected for rating")
                if subfield_rating not in valid_ratings:
                    raise ValueError(f"invalid rating for {field['tag']}${subfield['code']}: {subfield_rating}")

    def _is_complete(self, record: Record, rating: dict) -> bool:

        if rating.get("rating") not in HUMAN_RATINGS:
            return False

        selected = self._get_selected_fields()
        fields = rating.get("fields", {})

        for field in record.fields:
            if field["tag"] not in selected:
                continue

            field_rating = fields.get(str(field["id"]), {})

            if field_rating.get("rating") not in HUMAN_RATINGS:
                return False

            for subfield in field.get("subfields", []):
                if subfield["code"] not in selected[field["tag"]]:
                    continue

                rating = field_rating.get("subfields", {}).get(str(subfield["id"]))

                if rating not in HUMAN_RATINGS:
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

    def _build_info(self, record: Record, ratings: dict) -> dict:

        info = {}

        for field in record.fields:

            rating = ratings.get(str(field["id"]))
            if rating is None:
                continue

            tag = field["tag"]
            occurrences = info.setdefault(tag, [])
            occurrence = sum(f["tag"] == tag for f in record.fields[:field["id"]])

            while len(occurrences) <= occurrence:
                occurrences.append(None)

            occurrences[occurrence] = {
                "score": self._field_score(rating) if rating.get("rating") is not None else None,
                "rating": HUMAN_RATINGS[rating["rating"]] if rating.get("rating") is not None else None,
                "subfields": self._build_subfields(field, rating.get("subfields", {}))
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

    def _update_results(self, document_id: int, rating: dict, record: Record, all_completed: bool) -> None:

        path = self.output / "results.json"
        results = json.loads(path.read_text(encoding="utf-8"))

        result = next(result for result in results if result["id"] == document_id)
        result["methods"]["human-rating"] = {
            "score": self._document_score(rating),
            "rating": HUMAN_RATINGS[rating["rating"]],
            "info": self._build_info(record, rating.get("fields", {}))
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

    def save_document(self, document_id: int, rating: dict) -> bool:

        record = self._get_record(document_id)
        fields = rating.get("fields", {})
        self._validate_fields(record, fields)

        completed = self._is_complete(record, rating)
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
            self._update_results(document_id, rating, record, all_completed)

        return completed

    def initial_document(self) -> int:

        documents = self.load_ratings()["documents"]

        for document_id, document in documents.items():
            if not document["completed"]:
                return int(document_id)

        return max(len(documents) - 1, 0)