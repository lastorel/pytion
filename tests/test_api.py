import pytest

from pytion.models import Page, Block, Database, User
from pytion import InvalidRequestURL, ObjectNotFound


def test_notion(no):
    assert no.version == "2022-02-22"
    assert no.session.base == "https://api.notion.com/v1/"


class TestElement:
    def test_get__page(self, no):
        page = no.pages.get("878d628488d94894ab14f9b872cd6870")
        assert isinstance(page.obj, Page), "get of .pages. must return Page object"
        assert page.obj.id == "878d628488d94894ab14f9b872cd6870"
        assert str(page.obj.title) == "Pytion Tests"

    def test_get__block(self, no):
        block = no.blocks.get("878d628488d94894ab14f9b872cd6870")
        assert isinstance(block.obj, Block)
        assert block.obj.id == "878d628488d94894ab14f9b872cd6870"
        assert block.obj.text == "Pytion Tests"

    def test_get__database(self, no):
        database = no.databases.get("0e9539099cff456d89e44684d6b6c701")
        assert isinstance(database.obj, Database)
        assert database.obj.id == "0e9539099cff456d89e44684d6b6c701"
        assert str(database.obj.title) == "Little Database"

    def test_get__user(self, no):
        user = no.users.get("01c67faf3aba45ffaa022407f87c86a5")
        assert isinstance(user.obj, User)
        assert user.obj.id == "01c67faf3aba45ffaa022407f87c86a5"
        assert user.obj.name == "Yegor Gomzin"

    def test_get__bad_url(self, no):
        with pytest.raises(InvalidRequestURL):
            no.page.get("878d628488d94894ab14f9b872cd6870")

    def test_get__bad_id(self, no):
        with pytest.raises(ObjectNotFound):
            no.pages.get("878d628488d94894ab14f9b872cd6872")
