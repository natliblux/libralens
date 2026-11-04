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

            if not any(set(fields.get(tag, ())) & {"a", "b"} for tag in tags):
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

        return {
            "score": matched / len(entities) if entities else None,
            "info": results
        }