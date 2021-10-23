# -*- coding: utf-8 -*-

from typing import Optional, Union

import requests

from pytion.query import Request
from pytion.models import Database, Page, Block


Models = Union[Database, Page, Block]


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
        if "-" in id_:
            id_ = id_.replace("-", "")
        raw_obj = Request(self.api.session, method="get", path=self.name, id_=id_).result
        self.obj = self.class_map[raw_obj["object"]](**raw_obj)
        return self

    def get_parent(self, id_: Optional[str] = None):
        if isinstance(id_, str) and "-" in id_:
            id_ = id_.replace("-", "")
        if not self.obj:
            self.get(id_)
        if self.obj.object not in ("database", "page"):
            return None
        if self.obj.parent.uri:
            new_obj = Element(api=self.api, name=self.obj.parent.uri)
            return new_obj.get(self.obj.parent.id)
        return None

    def get_children(self, id_: Optional[str] = None):
        if self.name != "blocks":
            return None
        if isinstance(id_, str) and "-" in id_:
            id_ = id_.replace("-", "")
        if self.obj:
            id_ = self.obj.id
        child = Request(self.api.session, method="get", path=self.name, id_=id_, after_path="children").result
        # todo check child
        return Element(self.api, "blocks", child)

    def __repr__(self):
        if not self.obj:
            return f"Notion/{self.name}/"
        return f"Notion/{self.name}/{self.obj!r}"

    def __str__(self):
        return self.__repr__()

    def check_obj(self, obj):
        pass
    # todo
