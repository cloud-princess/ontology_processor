from pathlib import Path

import pytest

from question_processor import QuestionProcessor
from question_result import QuestionResult


@pytest.fixture
# The path returned will be used as the data file for all tests in this scope
def question_processor_data_file() -> Path:
    return Path("data/ontology.csv")


@pytest.mark.parametrize(
    ["entity", "attribute", "expected_result"],
    [
        ("hemlock", "poisonous", QuestionResult.YES),
        ("Lassie", "four-legged", QuestionResult.YES),
        # this should be yes because every element in the subclass belongs to the superclass
        # so it should have all the same attributes as the superclass
        ("killer whale", "warm-blooded", QuestionResult.YES),
        # classes can have attributes
        ("dog", "four-legged", QuestionResult.YES),
        ("Luna the Whale", "warm-blooded", QuestionResult.YES),
        # although it is obvious to humans that the answer is no
        # there is no data telling us whether Clifford is or isn't aquatic
        # Clifford is an instance of animal, which is a superclass to sea animals
        # which as attribute aquatic
        # although sea animals will have all the attributes of animals
        # the converse is not necessarily true
        ("Clifford the big red dog", "aquatic", QuestionResult.DONT_KNOW),
        ("sea animal", "poisonous", QuestionResult.DONT_KNOW),
        # pufferfish are a subclass of sea animal and should have all its attributes
        ("pufferfish", "aquatic", QuestionResult.YES),
        ("pufferfish", "warm-blooded", QuestionResult.DONT_KNOW),
        ("Luna the Whale", "aquatic", QuestionResult.YES),
        ("Uggie", "poisonous", QuestionResult.DONT_KNOW),
        ("killer whale", "four-legged", QuestionResult.DONT_KNOW),
        ("chicken", "four-legged", QuestionResult.DONT_KNOW),
        ("chicken", "warm0blooded", QuestionResult.DONT_KNOW),
        ########################################################
        # the following test cases are deliberately nonsensical
        # to test how the programme responds
        ########################################################
        # assume for the moment that an attribute cannot have attributes
        # and so an attribute cannot be its own attribute
        # however, autological words exist: 'pentasyllabic' is considered to be 'pentasyllabic'
        # maybe a more advanced OWL will be able to manage these relationships nicely
        ("poisonous", "poisonous", QuestionResult.NO),
        # 'is entity considered to be poisonous' is not the same as 'are all entities poisonous'
        # the question is not the latter, for which the answer is a definite no
        # but the former, which to me is a 'maybe'
        # a human would answer: it could be but not necessarily
        # closest answer we have to that is don't know
        ("entity", "poisonous", QuestionResult.DONT_KNOW),
        ("four-legged", "poisonous", QuestionResult.NO),
        # tree is not an attribute
        ("plant", "tree", QuestionResult.NO),
    ],
)
def test_is_considered_to_be(
    entity: str,
    attribute: str,
    expected_result: QuestionResult,
    question_processor: QuestionProcessor,
) -> None:
    assert expected_result == question_processor.process(
        f"is {entity} considered to be {attribute}?"
    )


@pytest.mark.parametrize(
    ["entity", "parent_class", "expected_result"],
    [
        # extension test
        ("Lassie", "plant", QuestionResult.NO)
        ("Ginger", "animal", QuestionResult.YES),
        # We don't know the answer to this because we don't have any data on pets
        ("Lassie", "pet", QuestionResult.DONT_KNOW),
        # Another example of the incompleteness of our data - from the data we have, we only know that Clifford is an
        # animal, we do not know that he is a dog.
        ("Clifford the Big Red Dog", "animal", QuestionResult.YES),
        ("Clifford the Big Red Dog", "dog", QuestionResult.DONT_KNOW),
        ########################################################
        # the following test cases are deliberately nonsensical
        # to test how the programme responds
        ########################################################
        # as we are not considering meta classes(whose instances are themselves classes)
        # an instance cannot be an instance of itself
        # an instnace cannot have instances
        ("General Sherman", "General Sherman", QuestionResult.NO),
        ("Lassie", "entity", QuestionResult.YES),
        ("entity", "entity", QuestionResult.NO),
        ("entity", "Lassie", QuestionResult.NO),
        ("General Sherman", "Lassie", QuestionResult.NO),
        # plant is a class, not an instance, so the answer is No.
        ("plant", "Lassie", QuestionResult.NO),
    ],
)
def test_is_instance(
    entity: str,
    parent_class: str,
    expected_result: QuestionResult,
    question_processor: QuestionProcessor,
) -> None:
    assert expected_result == question_processor.process(
        f"is {entity} a {parent_class}?"
    )


@pytest.mark.parametrize(
    ["entity", "parent_class", "expected_result"],
    [
        ("Ginger", "animal", QuestionResult.YES),
        ("Clifford the Big Red Dog", "animal", QuestionResult.YES),
    ],
)
def test_is_an_instance(  # todo rename: to make sure our code supports 'Is X an Y?'
    entity: str,
    parent_class: str,
    expected_result: QuestionResult,
    question_processor: QuestionProcessor,
) -> None:
    assert expected_result == question_processor.process(
        f"is {entity} an {parent_class}?"
    )


@pytest.mark.parametrize(
    ["child_class", "parent_class", "expected_result"],
    [
        # We don't know the answer because our data is incomplete - we may be missing a 'SubclassOf' edge between
        # 'pufferfish' and 'mammal', or it may be that this is false - we can't know purely based on our current data
        ("pufferfish", "mammal", QuestionResult.DONT_KNOW),
        # This is because we can't infer that the answer is "no" just because there is no connection - it may be that the connection is just missing from our data set.
        ("tree", "animal", QuestionResult.DONT_KNOW),
        ("sea animal", "animal", QuestionResult.YES),
        # According to W3's OWL reference, a class is a subclass of itself, so we return yes here
        # ref. https://www.w3.org/TR/owl-ref/
        ("plant", "plant", QuestionResult.YES),
        ("plant", "entity", QuestionResult.YES),
        ("entity", "entity", QuestionResult.YES),
        ########################################################
        # the following test cases are deliberately nonsensical
        # to test how the programme responds
        ########################################################
        # The question here is do we allow mutual subclasses i.e. a class to be a subclass of its own subclass.
        # If we do, then the answer here is don't know, because tree could well be a subclass of plant and we are just missing an edge.
        # Otherwise, it is no. Google has suggested that mutual subclasses exist in OWL ontologies,
        # so at this moment the answer has been set to don't know.
        ("plant", "tree", QuestionResult.DONT_KNOW),
    ],
)
def test_is_subclass(
    child_class: str,
    parent_class: str,
    expected_result: QuestionResult,
    question_processor: QuestionProcessor,
) -> None:
    assert expected_result == question_processor.process(
        f"is {child_class} a type of {parent_class}?"
    )


@pytest.mark.parametrize(
    ["entity", "attribute", "expected_result"],
    [
        # biennial does not exist in the ontology so we don't have enough data to answer
        ("hemlock", "biennial", QuestionResult.DONT_KNOW),
        # squirrel does not exist in the ontology so we don't have enough data to answer
        ("squirrel", "warm-blooded", QuestionResult.DONT_KNOW),
        # neither nodes exist in the ontology so we don't have enough data to answer
        ("squirrel", "cold-blooded", QuestionResult.DONT_KNOW),
    ],
)
def test_is_considered_to_be_not_enough_data(
    entity: str,
    attribute: str,
    expected_result: QuestionResult,
    question_processor: QuestionProcessor,
) -> None:
    assert expected_result == question_processor.process(
        f"is {entity} considered to be {attribute}?"
    )


@pytest.mark.parametrize(
    ["entity", "parent_class", "expected_result"],
    [
        # according to the ontology, Ginger is a chicken and as humans we know that chickens are not cats
        # but since cats are not in the ontology the program should not know the answer
        ("Ginger", "cat", QuestionResult.DONT_KNOW),
        # similarly, Terri the squirrel does not exist in the ontology
        ("Terri the squirrel", "mammal", QuestionResult.DONT_KNOW),
        # neither nodes exist in the ontology so we don't have enough data to answer
        ("Terri the squirrel", "goose", QuestionResult.DONT_KNOW),
    ],
)
def test_is_an_instance_not_enough_data(
    entity: str,
    parent_class: str,
    expected_result: QuestionResult,
    question_processor: QuestionProcessor,
) -> None:
    assert expected_result == question_processor.process(
        f"is {entity} a {parent_class}?"
    )


@pytest.mark.parametrize(
    ["child_class", "parent_class", "expected_result"],
    [
        # We don't know the answer because our data is incomplete - fish does not exist in the ontology
        ("pufferfish", "fish", QuestionResult.DONT_KNOW),
        # We don't know the answer because our data is incomplete - amphibian does not exist in the ontology
        ("amphibian", "animal", QuestionResult.DONT_KNOW),
        # Neither nodes exist in the ontology so we don't have enough data to answer
        ("amphibian", "vertebrates", QuestionResult.DONT_KNOW),
    ],
)
def test_is_subclass_not_enough_data(
    child_class: str,
    parent_class: str,
    expected_result: QuestionResult,
    question_processor: QuestionProcessor,
) -> None:
    assert expected_result == question_processor.process(
        f"is {child_class} a type of {parent_class}?"
    )


@pytest.mark.parametrize(
    ["question", "expected_result"],
    [
        ("how are pufferfish and fish related?", QuestionResult.DONT_KNOW),
        ("are pufferfish and fish related?", QuestionResult.DONT_KNOW),
        ("tell me how pufferfish and fish are related?", QuestionResult.DONT_KNOW),
        ("is pufferfish an instance of fish?", QuestionResult.DONT_KNOW),
    ],
)
def test_question_not_in_usual_format(
    question: str,
    expected_result: QuestionResult,
    question_processor: QuestionProcessor,
) -> None:
    # todo: nice to have - assert error log (look up how other people deal with this)
    assert expected_result == question_processor.process(question)