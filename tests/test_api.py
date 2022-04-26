from datetime import datetime

import pytest

from pytion.models import Page, Block, Database, User
from pytion.models import BlockArray, PropertyValue, PageArray, LinkTo, Property
from pytion import InvalidRequestURL, ObjectNotFound, ValidationError


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
        assert len(blocks.obj) == 3
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

    def test_get_parent__database_obj(self, little_database):
        database = little_database  # Little Database
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

    def test_get_block_children__page_obj(self, page_some_texts):
        page = page_some_texts  # Page with some texts
        blocks = page.get_block_children()
        assert isinstance(blocks.obj, BlockArray)
        assert len(blocks.obj) == 3
        assert isinstance(blocks.obj[0], Block)

    def test_get_block_children__block_id(self, no):
        blocks = no.blocks.get_block_children("8a920ba7dc1d4961811e5c82b28028ed")  # Hello! How are you?
        assert isinstance(blocks.obj, BlockArray)
        assert len(blocks.obj) == 3
        assert isinstance(blocks.obj[0], Block)

    def test_get_block_children__block_obj(self, no):
        block = no.blocks.get("8a920ba7dc1d4961811e5c82b28028ed")  # Hello! How are you?
        blocks = block.get_block_children()
        assert isinstance(blocks.obj, BlockArray)
        assert len(blocks.obj) == 3
        assert isinstance(blocks.obj[0], Block)

    def test_get_block_children__database_id(self, no):
        something = no.databases.get_block_children("0e9539099cff456d89e44684d6b6c701")  # Little Database
        assert something is None, "Database has no children"

    def test_get_block_children__database_obj(self, little_database):
        database = little_database  # Little Database
        something = database.get_block_children()
        assert something is None, "Database has no children"

    def test_get_block_children__child_database(self, no):
        database_block = no.blocks.get("0e9539099cff456d89e44684d6b6c701")  # Little Database
        database = database_block.get_block_children()
        assert isinstance(database.obj, Database)
        assert database.obj.id == "0e9539099cff456d89e44684d6b6c701"
        assert str(database.obj.title) == "Little Database"

    def test_get_block_children_recursive__page_id(self, no):
        blocks = no.pages.get_block_children_recursive("82ee5677402f44819a5da3302273400a")  # Page with some texts
        assert isinstance(blocks.obj, BlockArray)
        assert len(blocks.obj) == 6
        assert isinstance(blocks.obj[0], Block)

    def test_get_block_children_recursive__page_obj(self, page_some_texts):
        page = page_some_texts  # Page with some texts
        blocks = page.get_block_children_recursive()
        assert isinstance(blocks.obj, BlockArray)
        assert len(blocks.obj) == 6
        assert isinstance(blocks.obj[0], Block)

    def test_get_block_children_recursive__block_id(self, no):
        blocks = no.blocks.get_block_children_recursive("8a920ba7dc1d4961811e5c82b28028ed")  # Hello! How are you?
        assert isinstance(blocks.obj, BlockArray)
        assert len(blocks.obj) == 3
        assert isinstance(blocks.obj[0], Block)

    def test_get_block_children_recursive__block_obj(self, no):
        block = no.blocks.get("8a920ba7dc1d4961811e5c82b28028ed")  # Hello! How are you?
        blocks = block.get_block_children_recursive()
        assert isinstance(blocks.obj, BlockArray)
        assert len(blocks.obj) == 3
        assert isinstance(blocks.obj[0], Block)

    def test_get_block_children_recursive__database_id(self, no):
        something = no.databases.get_block_children_recursive("0e9539099cff456d89e44684d6b6c701")  # Little Database
        assert something is None, "Database has no children"

    def test_get_block_children_recursive__database_obj(self, little_database):
        database = little_database  # Little Database
        something = database.get_block_children_recursive()
        assert something is None, "Database has no children"

    def test_get_block_children_recursive__child_database(self, no):
        database_block = no.blocks.get("0e9539099cff456d89e44684d6b6c701")  # Little Database
        database = database_block.get_block_children_recursive()
        assert isinstance(database.obj, Database)
        assert database.obj.id == "0e9539099cff456d89e44684d6b6c701"
        assert str(database.obj.title) == "Little Database"

    def test_get_block_children_recursive__force(self, no):
        block = no.blocks.get("8a920ba7dc1d4961811e5c82b28028ed")  # Hello! How are you?
        blocks = block.get_block_children_recursive(force=True)
        assert isinstance(blocks.obj, BlockArray)
        assert len(blocks.obj) == 5
        assert isinstance(blocks.obj[0], Block)

    def test_get_block_children_recursive__max_depth(self, page_some_texts):
        page = page_some_texts  # Page with some texts
        blocks = page.get_block_children_recursive(force=True, max_depth=2)
        assert isinstance(blocks.obj, BlockArray)
        assert len(blocks.obj) == 7
        assert isinstance(blocks.obj[0], Block)

    def test_get_page_property__page_id(self, no):
        p = no.pages.get_page_property("%7Dma%3F", "b85877eaf7bf4245a8c5218055eeb81f")
        assert isinstance(p.obj, PropertyValue)
        assert len(p.obj.value) == 2
        assert p.obj.type == "multi_select"

    def test_get_page_property__page_obj(self, no):
        page = no.pages.get("b85877eaf7bf4245a8c5218055eeb81f")
        p = page.get_page_property("%7Dma%3F")
        assert isinstance(p.obj, PropertyValue)
        assert len(p.obj.value) == 2
        assert p.obj.type == "multi_select"

    def test_get_page_property__bad_id(self, no):
        with pytest.raises(ValidationError):
            no.pages.get_page_property("%7Dma%3A", "b85877eaf7bf4245a8c5218055eeb81f")

    def test_get_page_property__bad_page(self, no):
        with pytest.raises(ObjectNotFound):
            no.pages.get_page_property("%7Dma%3F", "b85877eaf7bf4245a8c5218055eeb81a")

    def test_db_query__id(self, no):
        pages = no.databases.db_query("0e9539099cff456d89e44684d6b6c701")  # Little Database
        assert isinstance(pages.obj, PageArray)
        assert len(pages.obj) == 4
        assert str(pages.obj[0].title) == ""

    def test_db_query__obj(self, little_database):
        pages = little_database.db_query(limit=3)
        assert isinstance(pages.obj, PageArray)
        assert len(pages.obj) == 3
        assert str(pages.obj[0].title) == ""

    def test_db_filter__title_ez(self, little_database):
        pages = little_database.db_filter("testing page")
        assert isinstance(pages.obj, PageArray)
        assert len(pages.obj) == 1
        assert str(pages.obj[0].title) == "Parent testing page"

    def test_db_filter__not_contain(self, little_database):
        pages = little_database.db_filter("testing page", condition="does_not_contain")
        assert isinstance(pages.obj, PageArray)
        assert len(pages.obj) == 3
        assert str(pages.obj[0].title) == ""

    def test_db_filter__ends_with(self, little_database):
        pages = little_database.db_filter(
            property_name="Name", property_type="title", value="what?", condition="ends_with"
        )
        assert isinstance(pages.obj, PageArray)
        assert len(pages.obj) == 1
        assert str(pages.obj[0].title) == "wait, what?"

    def test_db_filter__is_empty(self, little_database):
        pages = little_database.db_filter(property_name="title", property_type="title", condition="is_empty")
        assert isinstance(pages.obj, PageArray)
        assert len(pages.obj) == 1
        assert str(pages.obj[0].title) == ""

    def test_db_filter__greater_than(self, little_database):
        pages = little_database.db_filter(
            property_name="Digit", property_type="number", condition="greater_than", value="1"
        )
        assert isinstance(pages.obj, PageArray)
        assert len(pages.obj) == 2
        assert str(pages.obj[0].title) == "We are best friends, body"

    def test_db_filter__checkbox(self, little_database):
        pages = little_database.db_filter(property_name="Done", property_type="checkbox")
        assert isinstance(pages.obj, PageArray)
        assert len(pages.obj) == 1
        assert str(pages.obj[0].title) == "We are best friends, body"

    def test_db_filter__contains_tag(self, little_database):
        pages = little_database.db_filter(
            property_name="Tags", property_type="multi_select", value="tag1"
        )
        assert isinstance(pages.obj, PageArray)
        assert len(pages.obj) == 2
        assert str(pages.obj[0].title) == ""

    def test_db_filter__notcontains_tag(self, little_database):
        pages = little_database.db_filter(
            property_name="Tags", property_type="multi_select", value="tag2", condition="does_not_contain"
        )
        assert isinstance(pages.obj, PageArray)
        assert len(pages.obj) == 3
        assert str(pages.obj[0].title) == ""

    def test_db_filter__no_tags(self, little_database):
        pages = little_database.db_filter(
            property_name="Tags", property_type="multi_select", condition="is_empty"
        )
        assert isinstance(pages.obj, PageArray)
        assert len(pages.obj) == 1
        assert str(pages.obj[0].title) == "wait, what?"

    def test_db_filter__tag_property_obj(self, no, little_database):
        page = no.pages.get("c2fc6b3dc3d244e9be2a3d28b26082bf")  # Untitled
        my_prop = page.obj.properties["Tags"]
        pages = little_database.db_filter(property_obj=my_prop)
        assert isinstance(pages.obj, PageArray)
        assert len(pages.obj) == 2
        assert str(pages.obj[0].title) == ""

    def test_db_filter__without_filter(self, little_database):
        pages = little_database.db_filter("")
        assert isinstance(pages.obj, PageArray)
        assert len(pages.obj) == 4
        assert str(pages.obj[0].title) == ""

    def test_db_filter__date_after(self, little_database):
        pages = little_database.db_filter(
            property_name="created", property_type="date", condition="on_or_after", value="2022-04-22"
        )
        assert isinstance(pages.obj, PageArray)
        assert len(pages.obj) == 2
        assert str(pages.obj[0].title) == ""

    def test_db_filter__date_next_year(self, little_database):
        pages = little_database.db_filter(
            property_name="created", property_type="created_time", condition="next_year", value="2022-04-22"
        )
        assert isinstance(pages.obj, PageArray)
        assert len(pages.obj) == 0

    def test_db_filter__sort_desc(self, little_database):
        pages = little_database.db_filter("", descending="created")
        assert isinstance(pages.obj, PageArray)
        assert len(pages.obj) == 4
        assert str(pages.obj[0].title) == ""
        assert str(pages.obj[2].title) == "We are best friends, body"

    def test_db_filter__sort_asc(self, little_database):
        pages = little_database.db_filter("", ascending="Digit")
        assert isinstance(pages.obj, PageArray)
        assert len(pages.obj) == 4
        assert str(pages.obj[0].title) == "wait, what?"
        assert str(pages.obj[2].title) == "We are best friends, body"

    def test_db_create(self, no):
        parent = LinkTo.create(page_id="2dff77eb43d44ce097ffb421499f82aa")  # Page for creating databases
        properties = {
            "Name": Property.create("title"),
            "Digit": Property.create("number"),
            "Status": Property.create("select"),
        }
        title = "DB 1"
        database = no.databases.db_create(parent=parent, properties=properties, title=title)
        assert isinstance(database.obj, Database)
        assert str(database.obj.title) == title
        assert "Status" in database.obj.properties

        # Delete database manually. There is no way to delete a database by API

    def test_db_update__rename_title(self, database_for_updates):
        old_title = str(database_for_updates.obj.title)
        new_title = "1 BDU"
        database = database_for_updates.db_update(title=new_title)
        assert isinstance(database.obj, Database)
        assert str(database.obj.title) == new_title

        old_database = database_for_updates.db_update(title=old_title)
        assert str(old_database.obj.title) == old_title

    def test_db_update__rename_prop(self, database_for_updates):
        properties = {"Name": Property.create(type_="title", name="Subject")}
        database = database_for_updates.db_update(properties=properties)
        assert "Subject" in database.obj.properties

        title_property = database.obj.properties["Subject"]
        title_property.name = "Name"
        old_properties = {title_property.id: title_property}
        old_database = database.db_update(properties=old_properties)
        assert "Name" in old_database.obj.properties

    def test_db_update__retype_prop(self, database_for_updates):
        properties = {"Tags": Property.create("select")}
        database = database_for_updates.db_update(properties=properties)
        assert database.obj.properties["Tags"].type == "select"

        old_properties = {"Tags": Property.create("multi_select")}
        old_database = database_for_updates.db_update(properties=old_properties)
        assert old_database.obj.properties["Tags"].type == "multi_select"

    def test_db_update__create_delete_prop(self, database_for_updates):
        properties = {"New property": Property.create("checkbox")}
        database = database_for_updates.db_update(properties=properties)
        assert "New property" in database.obj.properties
        assert database.obj.properties["New property"].type == "checkbox"

        properties["New property"] = Property.create(None)
        database = database.db_update(properties=properties)
        assert "New property" not in database.obj.properties

    def test_page_create__into_page(self, no, page_for_pages):
        parent = LinkTo(from_object=page_for_pages.obj)
        page = no.pages.page_create(parent=parent, title="Page 1")
        assert isinstance(page.obj, Page)
        assert str(page.obj.title) == "Page 1"
        # delete section
        delete_page = page.page_update(archived=True)
        assert delete_page.obj.archived is True

    def test_page_create__into_database(self, no):
        parent = LinkTo.create(database_id="35f50aa293964b0d93e09338bc980e2e")  # Database for creating pages
        page = no.pages.page_create(parent=parent, title="Page 2")
        assert isinstance(page.obj, Page)
        assert str(page.obj.title) == "Page 2"
        # delete section
        delete_page = page.page_update(archived=True)
        assert delete_page.obj.archived is True

    def test_page_create__into_database_props(self, no):
        parent = LinkTo.create(database_id="35f50aa293964b0d93e09338bc980e2e")  # Database for creating pages
        props = {
            "Tags": PropertyValue.create(type_="multi_select", value=["tag1", "tag2"]),
            "done": PropertyValue.create("checkbox", True),
            "when": PropertyValue.create("date", datetime.now()),
        }
        page = no.pages.page_create(parent=parent, properties=props, title="Page 3")
        assert isinstance(page.obj, Page)
        assert str(page.obj.title) == "Page 3"
        # delete section
        delete_page = page.page_update(archived=True)
        assert delete_page.obj.archived is True

    def test_page_create__with_children(self, no, page_for_pages):
        parent = LinkTo(from_object=page_for_pages.obj)
        child = Block.create("Hello, World!")
        page = no.pages.page_create(parent=parent, title="Page 4", children=[child])
        assert isinstance(page.obj, Page)
        assert str(page.obj.title) == "Page 4"
        blocks = page.get_block_children()
        assert isinstance(blocks.obj, BlockArray)
        assert len(blocks.obj) == 1
        assert isinstance(blocks.obj[0], Block)
        assert str(blocks.obj[0].text) == "Hello, World!"
        # delete section
        delete_page = page.page_update(archived=True)
        assert delete_page.obj.archived is True

    def test_page_create__from_obj(self, no, page_for_pages):
        parent = LinkTo(from_object=page_for_pages.obj)
        page_obj = Page.create(parent=parent, title="Page 5")
        page = no.pages.page_create(page_obj=page_obj)
        assert isinstance(page.obj, Page)
        assert str(page.obj.title) == "Page 5"
        # delete section
        delete_page = page.page_update(archived=True)
        assert delete_page.obj.archived is True
