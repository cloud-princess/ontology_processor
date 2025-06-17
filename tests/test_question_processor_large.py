from pathlib import Path

import pytest

from question_processor import QuestionProcessor
from question_result import QuestionResult


@pytest.fixture
# The path returned will be used as the data file for all tests in this scope
def question_processor_data_file() -> Path:
    return Path("data/ontology-large.csv")


def test_baby_grand_is_a_type_of_musical_instrument(
    question_processor: QuestionProcessor,
) -> None:
    assert QuestionResult.YES == question_processor.process(
        "is baby grand a type of musical instrument?"
    )


def test_smirnoff_is_a_drink(question_processor: QuestionProcessor) -> None:
    assert QuestionResult.YES == question_processor.process("is Smirnoff a drink?")


def test_my_baby_grand_is_a_musical_instrument(
    question_processor: QuestionProcessor,
) -> None:
    assert QuestionResult.YES == question_processor.process(
        "is my baby grand a musical instrument?"
    )


def test_cheddar_is_hard(question_processor: QuestionProcessor) -> None:
    assert QuestionResult.YES == question_processor.process(
        "is Cheddar considered to be hard?"
    )


def test_my_baby_grand_is_playable(question_processor: QuestionProcessor) -> None:
    assert QuestionResult.YES == question_processor.process(
        "is my baby grand considered to be playable?"
    )
