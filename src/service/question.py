from __future__ import annotations  # For use-during-define in classmethod

from dataclasses import dataclass
from enum import Enum, auto
from re import compile


class QuestionType(Enum):
    SUBCLASS_OF = auto()
    INSTANCE_OF = auto()
    HAS_ATTRIBUTE = auto()


_QUESTION_PATTERNS = {
    QuestionType.SUBCLASS_OF: compile(r"is (.*) a type of (.*)\?"),
    QuestionType.INSTANCE_OF: compile(r"is (.*) (?:a|an) (.*)\?"),
    QuestionType.HAS_ATTRIBUTE: compile(r"is (.*) considered to be (.*)\?"),
}


class QuestionParsingException(Exception):
    pass


@dataclass
class Question:
    question_type: QuestionType
    head: str
    tail: str

    @classmethod
    def from_string(cls, question: str) -> Question:
        for question_type in QuestionType:
            pattern = _QUESTION_PATTERNS[question_type]
            match = pattern.fullmatch(question)

            if match is None:
                continue

            return cls(question_type, match.group(1), match.group(2))

        raise QuestionParsingException(f"Unable to parse question: {question}")