import json
from .base import BaseMethod
from ..constants import ENTITY_COVERAGE_SYSTEM_PROMPT, ENTITY_COVERAGE_USER_PROMPT

class EntityCoverageMethod(BaseMethod):

    name = "entity-coverage"

    supported_fields = {
        "100": ("a",),
        "110": ("a",),
        "700": ("a",),
        "710": ("a",)
    }

    requires_llm = True

    def run_doc(self, doc, fields, llm=None):

        results = {}

        groups = {
            "person": ("person", ("100", "700"), doc.eval.people_names),
            "corporate": ("corporate body", ("110", "710"), doc.eval.company_names)
        }

        for group, (entity_type, tags, names) in groups.items():

            if not any("a" in fields.get(tag, ()) for tag in tags):
                continue

            access_points = [name for tag in tags for name in names[tag]]

            user_prompt = ENTITY_COVERAGE_USER_PROMPT.replace("[ENTITY_TYPE]", entity_type).replace("[STATEMENT]", doc.eval.contributors or "").replace("[ENTITIES]", json.dumps(access_points, ensure_ascii=False))

            response = llm.run(system_prompt=ENTITY_COVERAGE_SYSTEM_PROMPT, user_prompt=user_prompt)
            response = response.strip()
            if response.startswith("```"):
                response = response.split("\n", 1)[1].rsplit("```", 1)[0].strip()
            results[group] = json.loads(response)

        entities = [entity for group in results.values() for entity in group]
        matched = sum(entity["matched"] for entity in entities)

        score = matched / len(entities) if entities else None

        return {
            "score": score,
            "references": {
                "none": {
                    "score": score,
                    **self.build_field_scores(results)
                }
            } if score is not None else {},
            "info": results
        }

    @staticmethod
    def build_field_scores(results: dict) -> dict:

        groups = {
            "person": "100/700",
            "corporate": "110/710"
        }

        scores = {}

        for group, entities in results.items():
            if not entities:
                continue

            score = sum(entity["matched"] for entity in entities) / len(entities)

            scores[groups[group]] = {
                "score": score,
                "a": score
            }

        return scores