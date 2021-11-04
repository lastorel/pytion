# -*- coding: utf-8 -*-

from typing import Optional, Union, Dict

import requests

from pytion.query import Request, Filter, Sort
from pytion.models import Database, Page, Block, BlockArray, PropertyValue, PageArray, LinkTo, RichTextArray, Property


Models = Union[Database, Page, Block, BlockArray, PropertyValue, PageArray]


class Notion(object):
    def __init__(self):
        self.session = requests.Session()

    def __len__(self):
        return 1

    # def __getstate__(self):
    #     return {"api": self.session}
    #
    # def __setstate__(self, d):
    #     self.__dict__.update(d)

    def __repr__(self):
        return "NotionAPI"

    def __str__(self):
        return self.__repr__()

    def __getattr__(self, name):
        # print(f"Getting {name}")
        return Element(self, name)


class Element(object):
    class_map = {"page": Page, "database": Database, "block": Block}

    def __init__(self, api: Notion, name: str, obj: Optional[Models] = None):
        # print(f"Creating Element({name})")
        self.api = api
        self.name = name
        self.obj = obj

    def get(self, id_: str):
        """
        Get Element by ID.
        .query.RequestError exception if not found
        """
        if "-" in id_:
            id_ = id_.replace("-", "")
        raw_obj = Request(self.api.session, method="get", path=self.name, id_=id_).result
        self.obj = self.class_map[raw_obj["object"]](**raw_obj)
        return self

    def get_parent(self, id_: Optional[str] = None):
        if not self.obj:
            self.get(id_)
        if getattr(self.obj, "parent"):
            new_obj = Element(api=self.api, name=self.obj.parent.uri)
            return new_obj.get(self.obj.parent.id)
        return None

    def get_block_children(self, id_: Optional[str] = None, limit: int = 0):
        if self.name != "blocks":
            return None
        if isinstance(id_, str) and "-" in id_:
            id_ = id_.replace("-", "")
        if self.obj:
            id_ = self.obj.id
        child = Request(
            self.api.session, method="get", path=self.name, id_=id_, after_path="children", limit=limit
        ).result
        # children object returns list of Blocks
        if child["object"] != "list":
            return None
        return Element(api=self.api, name="blocks", obj=BlockArray(child["results"]))

    def get_block_children_recursive(
        self, id_: Optional[str] = None, max_depth: int = 10, cur_depth: int = 0, limit: int = 0, force: bool = False
    ):
        """
        :param id_:
        :param max_depth:
        :param cur_depth:
        :param limit:
        :param force: get blocks in subpages too
        :return:
        """
        if self.name != "blocks":
            return None
        if isinstance(id_, str) and "-" in id_:
            id_ = id_.replace("-", "")
        if self.obj:
            id_ = self.obj.id
        child = Request(
            self.api.session, method="get", path=self.name, id_=id_, after_path="children", limit=limit
        ).result
        ba = BlockArray([])
        for b in child["results"]:
            block_obj = Block(level=cur_depth, **b)
            ba.append(block_obj)
            # Do not get subpages if not force
            if block_obj.type == "child_page" and not force:
                continue
            if block_obj.has_children and cur_depth < max_depth:
                sub_element = Element(api=self.api, name="blocks").get_block_children_recursive(
                    id_=block_obj.id, max_depth=max_depth, cur_depth=cur_depth+1, limit=limit
                )
                ba.extend(sub_element.obj)

        return Element(api=self.api, name="blocks", obj=ba)

    def get_page_property(self, property_id: str, id_: Optional[str] = None, limit: int = 0):
        if self.name != "pages":
            return None
        if isinstance(id_, str) and "-" in id_:
            id_ = id_.replace("-", "")
        if self.obj:
            id_ = self.obj.id
        property_obj = Request(
            self.api.session, method="get", path=self.name, id_=id_, after_path="properties/"+property_id, limit=limit
        ).result
        return Element(api=self.api, name=f"pages/{id_}/properties", obj=PropertyValue(property_obj, property_id))

    def db_query(
            self,
            id_: Optional[str] = None,
            limit: int = 0,
            filter_: Optional[Filter] = None,
            sorts: Optional[Sort] = None,
            **kwargs,
    ):
        if self.name != "databases":
            return None
        if isinstance(id_, str) and "-" in id_:
            id_ = id_.replace("-", "")
        if self.obj:
            id_ = self.obj.id
        r = Request(
            self.api.session, method="post", path=self.name, id_=id_, after_path="query",
            data={}, limit=limit, filter_=filter_, sorts=sorts
        ).result
        if r["object"] != "list":
            return None
        return Element(api=self.api, name="pages", obj=PageArray(r["results"]))

    def db_filter(self, **kwargs):
        """
        :param property_name: mandatory - full name or ID of property to filter by
        :param value: the value of this property to filter by (may be bool or datetime etc.)
        :param property_type: mandatory field - `text`, `number`, `checkbox`, `date`, `select` etc.
        :param condition: optional field - it depends on the type: `starts_with`, `contains`, `equals` etc.
        :param raw: correctly formatted dict to pass direct to API (instead all other params)
        :param property_obj: Property or PropertyValue obj. instead of `property_name` and `property_type`,
                             PropertyValue can put value in request, if `value` is not provided

        :param ascending: property name to be sorted by
        :param descending: property name to be sorted by

        :param limit: 0 < int < 100 - max number of items to be returned (0 = return all)

        examples
        `.db_filter(property_name="Done", property_type="checkbox", value=False, descending="title")`
        `.db_filter(property_name="tags", property_type="multi_select", condition="is_not_empty")`
        `.db_filter(raw=YOUR_BIG_DICT_FROM_NOTION_DOCS, limit=2)`

        Filters combinations does not supported. (in `raw` param only)
        """
        if self.name == "databases" and self.obj:
            sort = None
            if kwargs.get("ascending"):
                sort = Sort(property_name=kwargs["ascending"], direction="ascending")
            elif kwargs.get("descending"):
                sort = Sort(property_name=kwargs["descending"], direction="descending")
            filter_obj = Filter(**kwargs)
            return self.db_query(filter_=filter_obj, sorts=sort, **kwargs)
        return None

    def db_create(
            self, database_obj: Optional[Database] = None, parent: Optional[LinkTo] = None,
            properties: Optional[Dict[str, Property]] = None, title: Optional[Union[str, RichTextArray]] = None
    ):
        """
        :param database_obj:  you can provide `Database` object or -
                              provide the params for creating it:
        :param parent:
        :param properties:
        :param title:
        :return:
        """
        if self.name != "databases":
            return None
        if database_obj:
            db = database_obj
        else:
            if isinstance(title, str):
                title = RichTextArray.create(title)
            db = Database.create(parent=parent, properties=properties, title=title)
        created_db = Request(self.api.session, method="post", path=self.name, data=db.get()).result
        self.obj = Database(**created_db)
        return self

    def db_update(
            self, id_: Optional[str] = None, title: Optional[Union[str, RichTextArray]] = None,
            properties: Optional[Dict[str, Property]] = None
    ):
        """
        :param id_:         provide id of database if `self.obj` is empty
        :param title:       provide RichTextArray text to rename database
        :param properties:  provide dict of Property to update them
        :return:  self


        `rename_prop = Property.create(name="renamed")`
        `rename_retype_prop = Property.create(type_="multi_select", name="multiselected")`
        `retype_prop = Property.create("checkbox")`
        `props = {"Property1_name": rename_retype_prop, "Property2_ID": retype_prop}`
        `db = db.db_update(properties=props, title=RichTextArray.create("NEW DB"))`
        """
        if self.name != "databases":
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
        updated_db = Request(self.api.session, method="patch", path=self.name, id_=id_, data=patch).result
        self.obj = Database(**updated_db)
        return self

    def page_create(
            self, page_obj: Optional[Page] = None, parent: Optional[LinkTo] = None,
            properties: Optional[Dict[str, PropertyValue]] = None, title: Optional[Union[str, RichTextArray]] = None
    ):
        """
        :param page_obj:      you can provide `Database` object or -
                              provide the params for creating it:
        :param parent:        LinkTo object with ID of parent element
        :param properties:    Dict of properties with values
        :param title:         New title
        :return:

        `parent = LinkTo.create(database_id="24512345125123421")`
        `p2 = PropertyValue.create("date", datetime.now())`
        `r = no.pages.page_create(parent=parent, properties={"Count": p1, "Date": p2}, title="Всем привет")`

        `props["Status"] = PropertyValue.create("select", "new select option")`
        `props["Tags"] = PropertyValue.create("multi_select", ["new-option1", "new option2"])`
        `no.pages.create(parent=parent, properties=props)`

        `parent2 = LinkTo.create(page_id="64c6ab5c4b6a546b51ac684200b4f")`
        `no.pages.page_create(parent=parent2, title="New page 121")`
        """
        if self.name != "pages":
            return None
        if page_obj:
            page = page_obj
        else:
            page = Page.create(parent=parent, properties=properties, title=title)
        created_page = Request(self.api.session, method="post", path=self.name, data=page.get()).result
        self.obj = Page(**created_page)
        return self

    def page_update(
            self, id_: Optional[str] = None, properties: Optional[Dict[str, PropertyValue]] = None,
            title: Optional[Union[str, RichTextArray]] = None, archived: bool = False
    ):
        """
        :param id_:         ID of page
        :param properties:  dict of existing properties
        :param title:
        :param archived:    set `True` to delete the page
        :return:
        """
        if self.name != "pages":
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
        updated_page = Request(self.api.session, method="patch", path=self.name, id_=id_, data=patch).result
        self.obj = Page(**updated_page)
        return self

    def __repr__(self):
        if not self.obj:
            return f"Notion/{self.name}/"
        return f"Notion/{self.name}/{self.obj!r}"

    def __str__(self):
        return self.__repr__()
