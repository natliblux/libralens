from dataclasses import dataclass

@dataclass
class Run:
    method: str
    fields: list[str]