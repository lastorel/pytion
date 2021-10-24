# -*- coding: utf-8 -*-

from datetime import datetime
from typing import Optional, Dict, Union, List
from collections.abc import MutableSequence
# I wanna use pydantic, but API provide variable names of property


class RichText(object):
    def __init__(self, **kwargs) -> None:
        self.plain_text: str = kwargs.get("plain_text")
        self.href: Optional[str] = kwargs.get("href")
        self.annotations: Dict[str, Union[bool, str]] = kwargs.get("annotations")
        self.type: str = kwargs.get("type")
        self.data: Dict = kwargs[self.type]

    def __str__(self):
        return self.plain_text

    def __repr__(self):
        return f"RichText({self.plain_text})"

    def __len__(self):
        return len(self.plain_text)


class RichTextArray(MutableSequence):
    def __init__(self, array: List[Dict]) -> None:
        self.array = [RichText(**rt) for rt in array]

    def __getitem__(self, item):
        return self.array[item]

    def __setitem__(self, key, value):
        self.array[key] = value

    def __delitem__(self, key):
        del self.array[key]

    def __len__(self):
        return len(self.array)

    def insert(self, index: int, value) -> None:
        self.array.insert(index, value)

    def __str__(self):
        return " ".join(str(rt) for rt in self)

    def __repr__(self):
        return f"RichTextArray({str(self)})"


class Model(object):
    """
    :param id:
    :param object:
    :param created_time:
    :param last_edited_time:
    """
    def __init__(self, **kwargs) -> None:
        self.id = kwargs.get("id", "").replace("-", "")
        self.object = kwargs.get("object")
        self.created_time = self.format_iso_time(kwargs.get("created_time"))
        self.last_edited_time = self.format_iso_time(kwargs.get("last_edited_time"))
        self.raw = kwargs

    @classmethod
    def format_iso_time(cls, time: str) -> Optional[datetime]:
        if not time:
            return None
        return datetime.fromisoformat(time.replace("Z", "+00:00"))


class Property(object):
    def __init__(self, data: Dict[str, str]):
        self.id: str = data.get("id")
        self.type: str = data.get("type")
        self.name: str = data.get("name")
        self.raw = data

    def __str__(self):
        return self.name

    def __repr__(self):
        return f"Property({self})"


class PropertyValue(Property):
    def __init__(self, data: Dict, name: str):
        super().__init__(data)
        self.name = name
        # self.raw_value = data.get(self.type)

        if self.type == "title":
            self.value = RichTextArray(data["title"])

        if self.type == "rich_text":
            self.value = RichTextArray(data["rich_text"])

        if self.type == "number":
            self.value: Optional[int, float] = data["number"]

        if self.type == "select":
            if data["select"]:
                self.value: Optional[str] = data["select"].get("name")
            else:
                self.value = None

        if self.type == "multi_select":
            self.value: List[str] = [v.get("name") for v in data["multi_select"]]

        if self.type == "checkbox":
            self.value: bool = data["checkbox"]

        if self.type == "date":
            if data["date"]:
                self.value: Optional[str] = data["date"].get("start")
                self.start: Optional[datetime] = Model.format_iso_time(data["date"].get("start"))
                self.end: Optional[datetime] = Model.format_iso_time(data["date"].get("end"))
            else:
                self.value = None
                self.start = None
                self.end = None

        if "time" in self.type:
            self.value: Optional[datetime] = Model.format_iso_time(data.get(self.type))

        if self.type == "formula":
            formula_type = data["formula"]["type"]
            if formula_type == "date":
                if data["formula"]["date"]:
                    self.value: str = data["formula"]["date"].get("start")
                    self.start: Optional[datetime] = Model.format_iso_time(data["formula"]["date"].get("start"))
                    self.end: Optional[datetime] = Model.format_iso_time(data["formula"]["date"].get("end"))
                else:
                    self.value = None
                    self.start = None
                    self.end = None
            else:
                self.value: Union[str, int, float, bool] = data["formula"][formula_type]

        if self.type == "created_by":
            self.value = "unsupported"

        if self.type == "last_edited_by":
            self.value = "unsupported"

        if self.type == "people":
            self.value = "unsupported"

        if self.type == "relation":
            self.value: List[str] = [item.get("id") for item in data["relation"]]

        if self.type == "rollup":
            rollup_type = data["rollup"]["type"]
            if rollup_type == "array":
                if len(data["rollup"]["array"]) == 0:
                    self.value = None
                elif len(data["rollup"]["array"]) == 1:
                    self.value = PropertyValue(data["rollup"]["array"][0], rollup_type)
                else:
                    self.value = [PropertyValue(element, rollup_type) for element in data["rollup"]["array"]]

            if rollup_type == "number":
                self.value: Optional[int, float] = data["rollup"]["number"]

            if rollup_type == "date":
                self.value: Optional[str] = data["rollup"]["date"].get("start")
                self.start: Optional[datetime] = Model.format_iso_time(data["rollup"]["date"].get("start"))
                self.end: Optional[datetime] = Model.format_iso_time(data["rollup"]["date"].get("end"))

        if self.type == "files":
            self.value = "unsupported"

        if self.type == "url":
            self.value: Optional[str] = data.get("url")

        if self.type == "email":
            self.value: Optional[str] = data.get("email")

        if self.type == "phone_number":
            self.value: Optional[str] = data.get("phone_number")

    def __str__(self):
        return str(self.value)

    def __repr__(self):
        return f"{self.name}({self})"


class Database(Model):
    object = "database"
    path = "databases"

    def __init__(self, **kwargs) -> None:
        """
        params from Model +
        :param cover:
        :param icon:
        :param title:
        :param properties:
        :param parent:
        :param url:
        """
        super().__init__(**kwargs)
        self.cover: Optional[Dict] = kwargs.get("cover")
        self.icon: Optional[Dict] = kwargs.get("icon")
        self.title = RichTextArray(kwargs["title"])
        self.properties = {name: Property(value) for name, value in kwargs["properties"].items()}
        self._parent: Dict[str, str] = kwargs.get("parent")
        self.parent = LinkTo(**self._parent)
        self.url: str = kwargs.get("url")

    def __str__(self):
        return str(self.title)

    def __repr__(self):
        return f"Database({self.title})"


class Page(Model):
    object = "page"
    path = "pages"

    def __init__(self, **kwargs) -> None:
        """
        params from Model +
        :param cover:
        :param icon:
        :param parent:
        :param archived:
        :param properties:
        :param url:
        """
        super().__init__(**kwargs)
        self.cover: Optional[Dict] = kwargs.get("cover")
        self.icon: Optional[Dict] = kwargs.get("icon")
        self._parent: Dict[str, str] = kwargs.get("parent")
        self.parent = LinkTo(**self._parent)
        self.archived: bool = kwargs.get("archived")
        self.url: str = kwargs.get("url")
        self.properties = {name: PropertyValue(data, name) for name, data in kwargs["properties"].items()}
        for p in self.properties.values():
            if "title" in p.type:
                self.title = p.value
                break
        else:
            self.title = None

    def __str__(self):
        return str(self.title)

    def __repr__(self):
        return f"Page({self.title})"


class Block(Model):
    object = "block"
    path = "blocks"

    def __init__(self, **kwargs):
        """
        params from Model +
        :param has_children:
        :param type:
        :param archived:
        """
        super().__init__(**kwargs)
        self.type: str = kwargs.get("type")
        self.has_children: bool = kwargs.get("has_children")
        self.archived: bool = kwargs.get("archived")
        self.children = LinkTo(block=self)
        self._level = kwargs["level"] if kwargs.get("level") else 0
        self.parent = None

        if self.type == "paragraph":
            self.text = RichTextArray(kwargs[self.type].get("text"))
            # Paragraph Block does not contain `children` attr (watch Docs)

        if "heading" in self.type:
            self.text = RichTextArray(kwargs[self.type].get("text"))

        if self.type == "callout":
            self.text = RichTextArray(kwargs[self.type].get("text"))
            self.icon: Dict = kwargs[self.type].get("icon")
            # Callout Block does not contain `children` attr (watch Docs)

        if self.type == "quote":
            self.text = RichTextArray(kwargs[self.type].get("text"))
            # Quote Block does not contain `children` attr (watch Docs)

        if "list_item" in self.type:
            self.text = RichTextArray(kwargs[self.type].get("text"))
            # Block does not contain `children` attr (watch Docs)

        if self.type == "to_do":
            self.text = RichTextArray(kwargs[self.type].get("text"))
            self.checked: bool = kwargs[self.type].get("checked")
            # To-do Block does not contain `children` attr (watch Docs)

        if self.type == "toggle":
            self.text = RichTextArray(kwargs[self.type].get("text"))
            # Toggle Block does not contain `children` attr (watch Docs)

        if self.type == "code":
            self.text = RichTextArray(kwargs[self.type].get("text"))
            self.language: str = kwargs[self.type].get("language")

        if "child" in self.type:
            self.text = kwargs[self.type].get("title")
            if self.type == "child_page":
                self.parent = LinkTo(type="page", page=self.id)

        if self.type in ["embed", "image", "video", "file", "pdf", "breadcrumb"]:
            self.text = self.type

        if self.type == "bookmark":
            self.text: str = kwargs[self.type].get("url")
            self.caption = RichTextArray(kwargs[self.type].get("caption"))

        if self.type == "equation":
            self.text: str = kwargs[self.type].get("expression")

        if self.type == "divider":
            self.text = "---"

        if self.type == "table_of_contents":
            self.text = self.type

    def __str__(self):
        return str(self.text)

    def __repr__(self):
        return f"Block({str(self.text)[:30]})"


class ElementArray(MutableSequence):
    class_map = {"page": Page, "database": Database, "block": Block}

    def __init__(self, array):
        self.array = []
        for ele in array:
            if ele.get("object") and ele["object"] in self.class_map:
                self.array.append(self.class_map[ele["object"]](**ele))

    def __getitem__(self, item):
        return self.array[item]

    def __setitem__(self, key, value):
        self.array[key] = value

    def __delitem__(self, key):
        del self.array[key]

    def __len__(self):
        return len(self.array)

    def insert(self, index: int, value) -> None:
        self.array.insert(index, value)

    def __str__(self):
        return "\n".join(str(b) for b in self)

    def __repr__(self):
        r = str(self)[:30].replace("\n", " ")
        return f"ElementArray({r})"


class BlockArray(ElementArray):
    def __str__(self):
        return "\n".join(b._level * "\t" + str(b) for b in self)

    def __repr__(self):
        r = str(self)[:30].replace("\n", " ")
        return f"BlockArray({r})"


class PageArray(ElementArray):
    def __repr__(self):
        r = str(self)[:30].replace("\n", " ")
        return f"PageArray({r})"


class LinkTo(object):
    def __init__(self, block: Optional[Block] = None, **kwargs):
        if block:
            self.type = block.object
            self.id = block.id
            self.after_path = "children"
            self.uri = "blocks"
        else:
            self.type: str = kwargs.get("type")
            self.id: str = kwargs.get(self.type)
            self.after_path = ""
            if self.type == "page_id":
                self.uri = "blocks"
            elif self.type == "database_id":
                self.uri = "databases"
            # when type is set manually
            elif self.type == "page":
                self.uri = "pages"
            else:
                self.uri = None

        if isinstance(self.id, str):
            self.id = self.id.replace("-", "")
