# -*- coding: utf-8 -*-
from __future__ import annotations

import logging
from typing import Optional, Union, Dict, List

import pytion.envs as envs
from pytion.query import Request, Filter, Sort
from pytion.models import Database, Page, Block, BlockArray, PropertyValue, PageArray, LinkTo, RichTextArray, Property
from pytion.models import ElementArray, User


Models = Union[Database, Page, Block, BlockArray, PropertyValue, PageArray, ElementArray]
logger = logging.getLogger(__name__)


class Notion(object):
    def __init__(self, token: Optional[str] = None, version: Optional[str] = None):
        """
        Creates main API object.

        :param token:   provide your integration API token. If None - find the file `token`
        :param version: provide non hardcoded API version
        """
        self.version = version if version else envs.NOTION_VERSION
        self.session = Request(api=self, token=token)
        logger.debug(f"API object created. Version {envs.NOTION_VERSION}")

    def search(
            self, query: Optional[str] = None, limit: int = 0,
            object_type: Optional[str] = None, sort_last_edited_time: Optional[str] = None
    ) -> Optional[Element]:
        """
        Searches all original pages, databases, and child pages/databases that are shared with the integration.
        It will not return linked databases, since these duplicate their source databases. (c)


        :param query:                   search by page title
        :param limit:                   0 < int < 100 - max number of items to be returned (0 = return all)
        :param object_type:             filter by type: 'page' or 'database'
        :param sort_last_edited_time:   sorting 'ascending' or 'descending'
        :return:

        `r = no.search("pytion", 10, sort_last_edited_time="ascending")`
        `print(r.obj)`
        """
        data = {"query": query} if query else None
        filter_ = Filter(raw={"property": "object", "value": object_type}) if object_type else None
        if sort_last_edited_time:
            sort_last_edited_time = Sort(property_name="last_edited_time", direction=sort_last_edited_time)
        result = self.session.method(
            "post", "search", sort=sort_last_edited_time, filter_=filter_, limit=limit, data=data
        )
        if "results" in result and isinstance(result["results"], list):
            data = ElementArray(result["results"])
            for item in data:
                if isinstance(item, Page):
                    self.pages.get_page_properties(title_only=True, obj=item)
            return Element(api=self, name="search", obj=data)
        else:
            logger.warning("Results list is not found")
            return None

    def __len__(self):
        return 1

    def __repr__(self):
        return "NotionAPI"

    def __str__(self):
        return self.__repr__()

    def __getattr__(self, name):
        if name in dir(self):
            return self.name
        return Element(self, name)


class Element(object):
    class_map = {"page": Page, "database": Database, "block": Block, "user": User}

    def __init__(self, api: Notion, name: str, obj: Optional[Models] = None):
        self.api = api
        self.name = name
        self.obj = obj
        logger.debug(f"Element {self!r} created")

    def get(self, id_: str, _after_path: str = None, limit: int = 0) -> Element:
        """
        Get Element by ID.
        .exceptions.ObjectNotFound exception if not found

        :return:    `Element.obj` may be `Page`, `Database`, `Block`

        result = no.databases.get("1234123412341")
        result = no.pages.get("123412341234")
        result = no.blocks.get("123412341234")
        result = no.users.get("123412341234")
        print(result.obj)
        """
        if "-" in id_:
            id_ = id_.replace("-", "")
        if not _after_path:
            raw_obj = self.api.session.method(method="get", path=self.name, id_=id_, limit=limit)
        else:
            raw_obj = self.api.session.method(
                method="get", path=self.name, id_=id_, after_path=_after_path, limit=limit
            )
        if raw_obj["object"] == "list":
            if self.name == "pages":
                self.obj = PageArray(raw_obj["results"])
            elif self.name == "blocks":
                self.obj = BlockArray(raw_obj["results"])
            else:
                self.obj = ElementArray(raw_obj["results"])
        else:
            self.obj = self.class_map[raw_obj["object"]](**raw_obj)
        return self

    def get_parent(self, id_: Optional[str] = None) -> Optional[Element]:
        """
        Get parent object of current object if possible.

        :param id_:
        :return:    Element (parent object) or None. `.obj` may be `Page`, `Database`, `Block`

        `result = no.blocks.get_parent("123412341234")`
        `print(result)`
        Notion/pages/Page(Page Title here)
        `result = result.get_parent()`
        `print(result)`
        Notion/databases/Database(Some database name)
        """
        if not self.obj:
            self.get(id_)
        if getattr(self.obj, "parent", None):
            return self.from_linkto(self.obj.parent)
        logger.warning(f"Parent object can not be found")
        return None

    def get_block_children(
            self, id_: Optional[str] = None, block: Optional[Block] = None, limit: int = 0
    ) -> Optional[Element]:
        """
        Get children Block objects of current Block object (tabulated texts) if exist (else None)

        :param id_:
        :param block: you can provide a Block object instead to get his children
        :param limit:   0 < int < 100 - max number of items to be returned (0 = return all)
        :return:        `Element.obj` will be BlockArray object even nothing is found

        `print(no.pages.get_block_children("PAGE ID"))`
        None

        `print(no.blocks.get_block_children("PAGE ID"))`
        Notion/blocks/BlockArray(Heading 2 level Paragraph some)

        `print(no.blocks.get_block_children("PAGE ID").obj)`
        Heading 2 level
        Paragraph
        some text

        BlockArray or Database object expected.
        """
        if self.name not in ("blocks", "pages"):
            logger.warning("Only `blocks` or `pages` can have children")
            return None
        if isinstance(id_, str) and "-" in id_:
            id_ = id_.replace("-", "")
        obj = block if block else self.obj
        if obj:
            return self.from_linkto(obj.children, limit=limit)
        child = self.api.session.method(
            method="get", path="blocks", id_=id_, after_path="children", limit=limit
        )
        # children object returns list of Blocks
        if child["object"] != "list":
            logger.warning(f"List of Blocks expected. Received\n{child}")
            return None
        return Element(api=self.api, name="blocks", obj=BlockArray(child["results"]))

    def get_block_children_recursive(
        self, id_: Optional[str] = None, max_depth: int = 10, block: Optional[Block] = None,
        _cur_depth: int = 0, limit: int = 0, force: bool = False
    ) -> Optional[Element]:
        """
        Get children Block objects of current Block object (tabulated texts) if exist (else None) recursive

        :param id_:
        :param block:       you can provide a Block object instead to get his children
        :param max_depth:   how deep use the recursion (block inside block inside block etc.)
        :param limit:       0 < int < 100 - max number of items to be returned (0 = return all)
        :param force:       get blocks in subpages too
        :return:            `Element.obj` will be BlockArray object even nothing is found

        `print(no.blocks.get_block_children_recursive("PAGE ID").obj)`
        Heading 2 level
        Paragraph
            block inside block
        some text
        """
        if self.name not in ("blocks", "pages"):
            logger.warning("Only `blocks` or `pages` can have children")
            return None
        if isinstance(id_, str) and "-" in id_:
            id_ = id_.replace("-", "")
        obj = block if block else self.obj
        if obj:
            id_ = obj.id
            if isinstance(obj, Block) and obj.type == "child_database":
                return self.from_linkto(obj.children)
        child = self.api.session.method(
            method="get", path="blocks", id_=id_, after_path="children", limit=limit
        )
        ba = BlockArray([])
        for b in child["results"]:
            block_obj = Block(level=_cur_depth, **b)
            ba.append(block_obj)
            # Do not get subpages if not force
            if block_obj.type == "child_page" and not force:
                continue
            if block_obj.has_children and _cur_depth < max_depth:
                sub_element = Element(api=self.api, name="blocks").get_block_children_recursive(
                    id_=block_obj.id, max_depth=max_depth, _cur_depth=_cur_depth + 1, limit=limit, force=force
                )
                ba.extend(sub_element.obj)

        return Element(api=self.api, name="blocks", obj=ba)

    def get_page_property(self, property_id: str, id_: Optional[str] = None, limit: int = 0) -> Optional[Element]:
        """
        DEPRECATED
        Retrieve a page property item.

        :param property_id: ID of property in current database
        :param id_:         ID of page in that database (if not `self.obj`)
        :param limit:       0 < int < 100 - max number of items to be returned (0 = return all)
        :return:            `Element.obj` will be PropertyValue object

        `db = no.databases.get("1232412341234")`
        `property_id = db.obj.properties["Last edited time"].id`
        `result = no.pages.get_page_property(property_id, 'PAGE ID 152f123a12344')`
        `print(result.obj)`
        2021-11-04 16:47:00+00:00
        """
        if self.name != "pages":
            logger.warning("Only `pages` can have properties")
            return None
        if isinstance(id_, str) and "-" in id_:
            id_ = id_.replace("-", "")
        if self.obj and not id_:
            id_ = self.obj.id
        property_obj = self.api.session.method(
            method="get", path=self.name, id_=id_, after_path="properties/"+property_id, limit=limit
        )
        return Element(api=self.api, name=f"pages/{id_}/properties", obj=PropertyValue(property_obj, property_id))

    def get_page_properties(self, title_only: bool = False, obj: Optional[Page] = None) -> None:
        """
        Page properties must be retrieved using the page properties endpoint. (c)
        after retrieving a Page object you can retrieve its properties

        obj or self.obj must be a Page
        :return:
        """
        if not obj:
            obj = self.obj
        if obj and isinstance(obj, Page):
            for prop in obj.properties:
                # Skip already retrieved properties
                if isinstance(obj.properties[prop], PropertyValue):
                    continue
                prop_id = obj.properties[prop].id
                if title_only and prop_id != "title":
                    continue
                result = self.get_page_property(prop_id, id_=obj.id)
                obj.properties[prop] = result.obj
                if prop_id == "title":
                    obj.title = result.obj.value if result.obj.value else ""
            return
        logger.warning("You must provide a Page to retrieve properties")

    def db_query(
            self,
            id_: Optional[str] = None,
            limit: int = 0,
            filter_: Optional[Filter] = None,
            sorts: Optional[Sort] = None,
            **kwargs,
    ) -> Optional[Element]:
        if self.name != "databases":
            logger.warning("Only `databases` can be queried")
            return None
        if isinstance(id_, str) and "-" in id_:
            id_ = id_.replace("-", "")
        if self.obj:
            id_ = self.obj.id
        r = self.api.session.method(
            method="post", path=self.name, id_=id_, after_path="query",
            data={}, limit=limit, filter_=filter_, sorts=sorts
        )
        if r["object"] != "list":
            return None
        return Element(api=self.api, name="pages", obj=PageArray(r["results"]))

    def db_filter(self, title: str = None, **kwargs) -> Optional[Element]:
        """
        :param title: filter by title contains + opt. attrs: condition, sort etc.
        OR
        :param property_name: mandatory - full name or ID of property to filter by
        :param value: the value of this property to filter by (may be bool or datetime etc.)
        :param property_type: mandatory field - `text`, `number`, `checkbox`, `date`, `select` etc.
        :param condition: optional field - it depends on the type: `starts_with`, `contains`, `equals` etc.
        :param raw: correctly formatted dict to pass direct to API (instead of all other params)
        :param property_obj: Property or PropertyValue obj. instead of `property_name` and `property_type`,
                             PropertyValue can put value in request, if `value` is not provided

        :param ascending: property name to be sorted by
        :param descending: property name to be sorted by

        :param limit: 0 < int < 100 - max number of items to be returned (0 = return all)
        :return:              self.obj -> PageArray

        examples
        `.db_filter("My Page Title")`
        `.db_filter("", ascending="Tags")`
        `.db_filter(property_name="Done", property_type="checkbox")`
        `.db_filter(property_name="Done", property_type="checkbox", value=False, descending="title")`
        `.db_filter(property_name="tags", property_type="multi_select", condition="is_not_empty")`
        `.db_filter(raw=YOUR_BIG_DICT_FROM_NOTION_DOCS, limit=2)`

        Filters combinations are not supported. (in `raw` param only)
        """
        if self.name == "databases" and self.obj:
            sort = None
            if kwargs.get("ascending"):
                sort = Sort(property_name=kwargs["ascending"], direction="ascending")
            elif kwargs.get("descending"):
                sort = Sort(property_name=kwargs["descending"], direction="descending")
            if isinstance(title, str):
                filter_obj = Filter(property_name="title", value=title, property_type="title", **kwargs)
            else:
                filter_obj = Filter(**kwargs)
            return self.db_query(filter_=filter_obj, sorts=sort, **kwargs)
        logger.warning("Database must be provided. use .get() before")
        return None

    def db_create(
            self,
            database_obj: Optional[Database] = None,
            parent: Optional[LinkTo] = None,
            properties: Optional[Dict[str, Property]] = None,
            title: Optional[Union[str, RichTextArray]] = None,
            description: Optional[Union[str, RichTextArray]] = None,
    ) -> Optional[Element]:
        """
        :param database_obj:  you can provide `Database` object or -
                              provide the params for creating it:
        :param parent:        parent object in LinkTo format. workspace can not be a parent
        :param properties:    dict of properties. Property with `title` type is mandatory!
        :param title:         your name of the Database
        :param description:   optional description for new Database
        :return:              self.obj -> Database

        `parent = LinkTo.create(database_id="24512345125123421")`
        `p1 = Property.create(name="renamed")`
        `p2 = Property.create(type_="multi_select", name="multiselected")`
        `props = {"Property1_name": p1, "Property2_name": p2}` OR
        ```props = {
            "Name": Property.create("title")
            "Digit": Property.create("number"),
            "Status": Property.create("select")
        }```
        `db = db.db_create(parent=parent, properties=props, title=RichTextArray.create("NEW DB"))`
        """
        if self.name != "databases":
            logger.warning("Method supports `databases` only")
            return None
        if database_obj:
            db = database_obj
        else:
            if isinstance(title, str):
                title = RichTextArray.create(title)
            db = Database.create(parent=parent, properties=properties, title=title, description=description)
        created_db = self.api.session.method(method="post", path=self.name, data=db.get())
        self.obj = Database(**created_db)
        return self

    def db_update(
            self, id_: Optional[str] = None, title: Optional[Union[str, RichTextArray]] = None,
            properties: Optional[Dict[str, Property]] = None
    ) -> Optional[Element]:
        """
        :param id_:         provide id of database if `self.obj` is empty
        :param title:       provide RichTextArray or text to rename database
        :param properties:  provide dict of Property to update them
        :return:            self.obj -> Database


        `rename_prop = Property.create(name="renamed")`
        `rename_retype_prop = Property.create(type_="multi_select", name="multiselected")`
        `retype_prop = Property.create("checkbox")`
        `props = {"Property1_name": rename_retype_prop, "Property2_ID": retype_prop}`
        `db = db.db_update(properties=props, title=RichTextArray.create("NEW DB"))`
        """
        if self.name != "databases":
            logger.warning("Method supports `databases` only")
            return None
        if isinstance(id_, str) and "-" in id_:
            id_ = id_.replace("-", "")
        if self.obj:
            id_ = self.obj.id
        patch = {}
        if title:
            if isinstance(title, str):
                title = RichTextArray.create(title)
            patch["title"] = title.get()
        if properties:
            patch["properties"] = {name: value.get() for name, value in properties.items()}
        updated_db = self.api.session.method(method="patch", path=self.name, id_=id_, data=patch)
        self.obj = Database(**updated_db)
        return self

    def page_create(
            self,
            page_obj: Optional[Page] = None,
            parent: Optional[LinkTo] = None,
            properties: Optional[Dict[str, PropertyValue]] = None,
            title: Optional[Union[str, RichTextArray]] = None,
            children: Union[BlockArray, List[Block], None] = None,
    ) -> Optional[Element]:
        """
        :param page_obj:      you can provide `Page` object or -
                              provide the params for creating it:
        :param parent:        LinkTo object with ID of parent element. workspace can not be a parent
        :param properties:    Dict of properties with values
        :param title:         New title
        :param children:      Content of new page in [Block] or BlockArray format
        :return:              self.obj -> Page

        `parent = LinkTo.create(database_id="24512345125123421")`
        `p2 = PropertyValue.create("date", datetime.now())`
        `r = no.pages.page_create(parent=parent, properties={"Count": p1, "Date": p2}, title="Extra PAGE")`

        `props["Status"] = PropertyValue.create("select", "new select option")`
        `props["Tags"] = PropertyValue.create("multi_select", ["new-option1", "new option2"])`
        `no.pages.create(parent=parent, properties=props)`

        `parent2 = LinkTo.create(page_id="123412341234")`
        `no.pages.page_create(parent=parent2, title="New page 121")`
        """
        if self.name != "pages":
            logger.warning("Method supports `pages` only")
            return None
        if page_obj:
            page = page_obj
        else:
            if children and not isinstance(children, BlockArray):
                children = BlockArray(children, create=True)
            page = Page.create(parent=parent, properties=properties, title=title, children=children)
        created_page = self.api.session.method(method="post", path=self.name, data=page.get())
        self.obj = Page(**created_page)
        return self

    def page_update(
            self, id_: Optional[str] = None, properties: Optional[Dict[str, PropertyValue]] = None,
            title: Optional[Union[str, RichTextArray]] = None, archived: bool = False
    ) -> Optional[Element]:
        """
        :param id_:         ID of page
        :param properties:  dict of existing properties
        :param title:
        :param archived:    set to `True` for delete the page
        :return:            self.obj -> Page
        """
        if self.name != "pages":
            logger.warning("Method supports `pages` only")
            return None
        if isinstance(id_, str) and "-" in id_:
            id_ = id_.replace("-", "")
        if self.obj:
            id_ = self.obj.id
        patch = {}
        if properties:
            patch["properties"] = {name: p.get() for name, p in properties.items()}
        if title:
            patch.setdefault("properties", {})
            patch["properties"]["title"] = PropertyValue.create("title", title).get()
        # if archived:
        patch["archived"] = archived
        updated_page = self.api.session.method(method="patch", path=self.name, id_=id_, data=patch)
        self.obj = Page(**updated_page)
        return self

    def block_update(
            self, id_: Optional[str] = None, block_obj: Optional[Block] = None,
            new_text: Optional[str] = None, archived: bool = False
    ) -> Optional[Element]:
        """
        Updates text of Block.
        `text`, `checked` (`to_do` type), `language` (`code` type) fields support only!
        You can modify any attrs of existing block and provide it (Block object) to this func.
        Changing the Block type is not supported.

        :param id_:         ID of block to change text OR
        :param block_obj:   modified Block (replace mode only)

        :param new_text:    new text (replace mode only)
        :param archived:    flag to delete that Block
        :return:            self.obj -> Block

        `blocks = no.blocks.get_block_children("PAGE ID")`
        `for b in blocks.obj:`
            `no.blocks.block_update(block_obj=b, new_text="OH YEEEAHH")`
        `for b in blocks.obj:`
            `b.text = "ALL IS DONE"`
            `no.blocks.block_update(block_obj=b)`
        """
        if self.name != "blocks":
            logger.warning("Method supports `blocks` only")
            return None
        if isinstance(id_, str) and "-" in id_:
            id_ = id_.replace("-", "")
        if self.obj:
            id_ = self.obj.id
        else:
            self.get(id_)
        if block_obj:
            self.obj = block_obj
        if not self.obj.get():
            return None
        if new_text:
            self.obj.text = new_text
        patch = {"archived": archived}
        patch.update(self.obj.get())
        updated_block = self.api.session.method(method="patch", path=self.name, id_=id_, data=patch)
        self.obj = Block(**updated_block)
        return self

    def block_append(
            self, id_: Optional[str] = None, block: Optional[Block] = None,
            blocks: Union[BlockArray, List[Block], None] = None
    ) -> Optional[Element]:
        """
        Append block or blocks children

        :param id_:         provide id of block or page if `self.obj` is empty

        :param block:       Block to append OR
        :param blocks:          List[Block] or BlockArray to append

        :return:            self.obj -> BlockArray

        `p1 = no.pages.get("PAGE ID")`
        `p1.block_append(block=Block.create("SOMETHING NEW YO"))`

        `no.blocks.block_append("BLOCK OR PAGE ID", blocks=blocks)`
        """
        if self.name not in ["blocks", "pages"]:
            logger.warning("Method supports `blocks` or `pages` only")
            return None
        if isinstance(id_, str) and "-" in id_:
            id_ = id_.replace("-", "")
        if self.obj:
            id_ = self.obj.id
        if isinstance(blocks, list):
            blocks = BlockArray(blocks, create=True)
        if isinstance(block, Block):
            blocks = BlockArray([block], create=True)
        data = {"children": blocks.get()}

        new_blocks = self.api.session.method(
            method="patch", path="blocks", id_=id_, after_path="children", data=data
        )
        return Element(api=self.api, name="blocks", obj=BlockArray(new_blocks["results"]))

    def get_myself(self) -> Element:
        """
        Retrieves the bot User associated with the API token provided in the authorization header.

        :return: Element with User obj

        `me = no.users.get_myself()`
        """
        new_object = Element(self.api, name="users")
        new_object.get("me")
        return new_object

    def from_linkto(self, linkto: LinkTo, limit: int = 0) -> Optional[Element]:
        if not linkto:
            logger.error("LinkTo must be provided!")
            return None
        if not linkto.uri:
            logger.error("LinkTo.uri must be provided!")
            return None
        new_element = Element(self.api, name=linkto.uri)
        return new_element.get(linkto.id, getattr(linkto, "after_path", None), limit)

    def from_object(self, model: Union[Database, Page, Block]):
        return Element(self.api, model.path, model)

    def __repr__(self):
        if not self.obj:
            return f"Notion/{self.name}/"
        return f"Notion/{self.name}/{self.obj!r}"

    def __str__(self):
        return self.__repr__()
