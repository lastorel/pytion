import pytest

from pytion.models import Page, Block, Database, User
from pytion.models import BlockArray
from pytion import InvalidRequestURL, ObjectNotFound


def test_notion(no):
    assert no.version == "2022-02-22"
    assert no.session.base == "https://api.notion.com/v1/"


class TestElement:
    def test_get__page(self, root_page):
        page = root_page
        assert isinstance(page.obj, Page), "get of .pages. must return Page object"
        assert page.obj.id == "878d628488d94894ab14f9b872cd6870"
        assert str(page.obj.title) == "Pytion Tests"

    def test_get__block(self, no):
        block = no.blocks.get("878d628488d94894ab14f9b872cd6870")  # root page
        assert isinstance(block.obj, Block)
        assert block.obj.id == "878d628488d94894ab14f9b872cd6870"
        assert block.obj.text == "Pytion Tests"

    def test_get__database(self, no):
        database = no.databases.get("0e9539099cff456d89e44684d6b6c701")  # Little Database
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
            no.page.get("878d628488d94894ab14f9b872cd6870")  # root page

    def test_get__bad_id(self, no):
        with pytest.raises(ObjectNotFound):
            no.pages.get("878d628488d94894ab14f9b872cd6872")  # random id

    def test_get__after_path_page(self, no):
        blocks = no.blocks.get("82ee5677402f44819a5da3302273400a", _after_path="children")  # Page with some texts
        assert isinstance(blocks.obj, BlockArray)
        assert len(blocks.obj) == 3
        assert isinstance(blocks.obj[0], Block)
        blocks = no.blocks.get("82ee5677402f44819a5da3302273400a", _after_path="children", limit=2)  # Page with some te
        assert len(blocks.obj) == 2

    def test_get__after_path_block(self, no):
        blocks = no.blocks.get("8a920ba7dc1d4961811e5c82b28028ed", _after_path="children")  # Hello! How are you?
        assert isinstance(blocks.obj, BlockArray)
        assert len(blocks.obj) == 1
        assert isinstance(blocks.obj[0], Block)

    def test_get_parent__block(self, no):
        something = no.blocks.get_parent("9b2026c3a0cb45fc8cee330142d60f3a")  # I'm fine!
        assert something is None, "Blocks have not any parent"

    def test_get_parent__page(self, no):
        parent_page_block = no.pages.get_parent("82ee5677402f44819a5da3302273400a")  # Page with some texts
        assert isinstance(parent_page_block.obj, Block)
        assert parent_page_block.obj.id == "878d628488d94894ab14f9b872cd6870"
        assert parent_page_block.obj.text == "Pytion Tests"

    def test_get_parent__database(self, no):
        parent_page_block = no.pages.get_parent("82ee5677402f44819a5da3302273400a")  # Little Database
        assert isinstance(parent_page_block.obj, Block)
        assert parent_page_block.obj.id == "878d628488d94894ab14f9b872cd6870"
        assert parent_page_block.obj.text == "Pytion Tests"

    def test_get_parent__user(self, no):
        something = no.users.get_parent("01c67faf3aba45ffaa022407f87c86a5")
        assert something is None, "User object has not any parent"

    def test_get_parent__block_obj(self, no):
        block = no.blocks.get("8a920ba7dc1d4961811e5c82b28028ed")  # Hello! How are you?
        assert block.get_parent() is None, "Blocks have not any parent"

    def test_get_parent__page_obj(self, no):  # Database is the parent of this page
        page = no.pages.get("b85877eaf7bf4245a8c5218055eeb81f")  # Parent testing page
        database = page.get_parent()
        assert isinstance(database.obj, Database)
        assert database.obj.id == "0e9539099cff456d89e44684d6b6c701"
        assert str(database.obj.title) == "Little Database"

    def test_get_parent__database_obj(self, no):
        database = no.databases.get("0e9539099cff456d89e44684d6b6c701")  # Little Database
        parent_page_block = database.get_parent()
        assert isinstance(parent_page_block.obj, Block)
        assert parent_page_block.obj.id == "878d628488d94894ab14f9b872cd6870"
        assert parent_page_block.obj.text == "Pytion Tests"

    def test_get_parent__child_page(self, no):
        child_page = no.blocks.get("878d628488d94894ab14f9b872cd6870")  # root page
        page = child_page.get_parent()
        assert isinstance(page.obj, Page)
        assert page.obj.id == "878d628488d94894ab14f9b872cd6870"
        assert str(page.obj.title) == "Pytion Tests"

    def test_get_parent__child_database(self, no):
        child_database = no.blocks.get("0e9539099cff456d89e44684d6b6c701")  # Little Database
        database = child_database.get_parent()
        assert isinstance(database.obj, Database)
        assert database.obj.id == "0e9539099cff456d89e44684d6b6c701"
        assert str(database.obj.title) == "Little Database"

    def test_get_parent__workspace(self, root_page):
        workspace = root_page.get_parent()
        assert workspace is None

    def test_get_block_children__page_id(self, no):
        blocks = no.pages.get_block_children("82ee5677402f44819a5da3302273400a")  # Page with some texts
        assert isinstance(blocks.obj, BlockArray)
        assert len(blocks.obj) == 3
        assert isinstance(blocks.obj[0], Block)

    def test_get_block_children__page_obj(self, no):
        page = no.pages.get("82ee5677402f44819a5da3302273400a")  # Page with some texts
        blocks = page.get_block_children()
        assert isinstance(blocks.obj, BlockArray)
        assert len(blocks.obj) == 3
        assert isinstance(blocks.obj[0], Block)

    def test_get_block_children__block_id(self, no):
        blocks = no.blocks.get_block_children("8a920ba7dc1d4961811e5c82b28028ed")  # Hello! How are you?
        assert isinstance(blocks.obj, BlockArray)
        assert len(blocks.obj) == 1
        assert isinstance(blocks.obj[0], Block)

    def test_get_block_children__block_obj(self, no):
        block = no.blocks.get("8a920ba7dc1d4961811e5c82b28028ed")  # Hello! How are you?
        blocks = block.get_block_children()
        assert isinstance(blocks.obj, BlockArray)
        assert len(blocks.obj) == 1
        assert isinstance(blocks.obj[0], Block)

    def test_get_block_children__database_id(self, no):
        something = no.databases.get_block_children("0e9539099cff456d89e44684d6b6c701")  # Little Database
        assert something is None, "Database has no children"

    def test_get_block_children__database_obj(self, no):
        database = no.databases.get("0e9539099cff456d89e44684d6b6c701")  # Little Database
        something = database.get_block_children()
        assert something is None, "Database has no children"

    def test_get_block_children__child_database(self, no):
        database_block = no.blocks.get("0e9539099cff456d89e44684d6b6c701")  # Little Database
        database = database_block.get_block_children()
        assert isinstance(database.obj, Database)
        assert database.obj.id == "0e9539099cff456d89e44684d6b6c701"
        assert str(database.obj.title) == "Little Database"
