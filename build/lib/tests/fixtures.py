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


@pytest.fixture(scope="session")
def database_for_updates(no):
    return no.databases.get("bf6ee5f75f99433a9d65132c05b42958")


@pytest.fixture(scope="session")
def page_for_pages(no):
    return no.pages.get("1bc86cc1d6f24362a6c40c2c89b423cc")


@pytest.fixture(scope="session")
def page_for_updates(no):
    page = no.pages.get("36223246a20e42df8f9b354ed1f11d75")
    return page
