import pytest


@pytest.fixture(scope="session")
def root_page(no):
    return no.pages.get("878d628488d94894ab14f9b872cd6870")
