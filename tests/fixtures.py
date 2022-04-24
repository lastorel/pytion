import pytest


@pytest.fixture(scope="session")
def root_page(no):
    return no.pages.get("878d628488d94894ab14f9b872cd6870")


@pytest.fixture(scope="session")
def page_some_texts(no):
    return no.pages.get("82ee5677402f44819a5da3302273400a")


@pytest.fixture(scope="session")
def little_database(no):
    return no.databases.get("0e9539099cff456d89e44684d6b6c701")
