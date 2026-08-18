from enum import Enum

class InputFormat(str, Enum):
    
    TEXT = "txt"
    XML = "xml"

    @property
    def extension(self) -> str:
        return {
            InputFormat.TEXT: ".txt",
            InputFormat.XML: ".xml",
        }[self]