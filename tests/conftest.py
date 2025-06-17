from pathlib import Path

import pytest

from question_processor import QuestionProcessor


@pytest.fixture
def question_processor(question_processor_data_file: Path):
    return QuestionProcessor(question_processor_data_file)
