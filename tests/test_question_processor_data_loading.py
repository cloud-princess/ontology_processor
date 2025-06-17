from pathlib import Path

import pandas as pd
import pytest

from question_processor import QuestionProcessor
from question_result import QuestionResult


@pytest.fixture
# The path returned will be used as the data file for all tests in this scope
def question_processor_data_file() -> Path:
    return Path("data/test-ontology.csv")


def test_load_data_tail_indexed(
    question_processor: QuestionProcessor,
    question_processor_data_file: Path,
) -> None:
    expected_df = pd.DataFrame(
        [["SubclassOf", "organism"], ["SubclassOf", "plant"]],
        index=["entity", "organism"],
        columns=["EDGE_TYPE", "HEAD_ENTITY"],
    )
    result = question_processor.load_data(
        question_processor_data_file, index="TAIL_ENTITY"
    )
    assert expected_df.equals(result)


def test_load_data_head_indexed(
    question_processor: QuestionProcessor,
    question_processor_data_file: Path,
) -> None:
    expected_df = pd.DataFrame(
        [["SubclassOf", "entity"], ["SubclassOf", "organism"]],
        index=["organism", "plant"],
        columns=["EDGE_TYPE", "TAIL_ENTITY"],
    )
    result = question_processor.load_data(
        question_processor_data_file, index="HEAD_ENTITY"
    )
    assert expected_df.equals(result)
