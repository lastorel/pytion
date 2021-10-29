# -*- coding: utf-8 -*-

from typing import Optional, Union

import requests

from pytion.query import Request, Filter, Sort
from pytion.models import Database, Page, Block, BlockArray, PropertyValue, PageArray


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
        print(f"Getting {name}")
        return Element(self, name)


class Element(object):
    class_map = {"page": Page, "database": Database, "block": Block}

    def __init__(self, api: Notion, name: str, obj: Optional[Models] = None):
        print(f"Creating Element({name})")
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

    def get_children(self, id_: Optional[str] = None, limit: int = 0):
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

    def get_children_recursive(
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
                sub_element = Element(api=self.api, name="blocks").get_children_recursive(
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

    def query_database(
            self,
            id_: Optional[str] = None,
            limit: int = 0,
            filter_: Optional[Filter] = None,
            sorts: Optional[Sort] = None,
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

    def filter(self, **kwargs):
        """
        :param property_name: mandatory - full name or ID of property to filter by
        :param value: the value of this property to filter by (may be bool or datetime etc.)
        :param property_type: mandatory field - `text`, `number`, `checkbox`, `date`, `select` etc.
        :param condition: optional field - it depends on the type: `starts_with`, `contains`, `equals` etc.
        :param raw: correctly formatted dict to pass to API (instead all other params)

        :param ascending: property name to be sorted by
        :param descending: property name to be sorted by

        example
        `.filter(property_name="Done", property_type="checkbox", value=False, descending="title")`
        `.filter(property_name="tags", property_type="multi_select", condition="is_not_empty")`

        Filters combinations does not supported.
        """
        if self.name == "databases" and self.obj:
            sort = None
            if kwargs.get("ascending"):
                sort = Sort(property_name=kwargs["ascending"], direction="ascending")
            elif kwargs.get("descending"):
                sort = Sort(property_name=kwargs["descending"], direction="descending")
            filter_obj = Filter(**kwargs)
            return self.query_database(filter_=filter_obj, sorts=sort)
        return None

    def __repr__(self):
        if not self.obj:
            return f"Notion/{self.name}/"
        return f"Notion/{self.name}/{self.obj!r}"

    def __str__(self):
        return self.__repr__()
