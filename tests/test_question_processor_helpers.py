from pathlib import Path

import pandas as pd
import pytest

from question_processor import QuestionProcessor


@pytest.fixture
# The path returned will be used as the data file for all tests in this scope
def question_processor_data_file() -> Path:
    return Path("data/test-ontology.csv")


def test_edges(
    question_processor: QuestionProcessor,
) -> None:
    expected_df = pd.DataFrame(
        [["SubclassOf", "organism"]],
        index=["plant"],
        columns=["EDGE_TYPE", "TAIL_ENTITY"],
    )
    result = question_processor._edges("plant", head_indexed=True)
    assert expected_df.equals(result)

@pytest.mark.parametrize(
    ["node", "expected_result"],
    [
        ("entity", False),
        ("plant", True),
    ],
)
def test_has_parents(
    question_processor: QuestionProcessor,
    node: str,
    expected_result: bool,
) -> None:
    result = question_processor._has_parents(node)
    assert expected_result == result
