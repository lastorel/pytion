# -*- coding: utf-8 -*-
from __future__ import annotations
from datetime import datetime
from typing import Optional, Dict, Union, List, Any
from collections.abc import MutableSequence

from pytion.envs import NOTION_URL


# I wanna use pydantic, but API provide variable names of property

class RichText(object):
    def __init__(self, **kwargs) -> None:
        self.plain_text: str = kwargs.get("plain_text")
        self.href: Optional[str] = kwargs.get("href")
        self.annotations: Dict[str, Union[bool, str]] = kwargs.get("annotations")
        # if not self.annotations:
        #     self._create_default_annotations()
        self.type: str = kwargs.get("type")
        self.simple = ""
        if self.type == "mention":
            subtype = kwargs[self.type].get("type")
            if subtype == "user":
                self.data = User(**kwargs[self.type].get(subtype))
                self.plain_text = str(self.data)
                self.simple = LinkTo(from_object=self.data).link
            elif subtype == "page":
                sub_id = kwargs[self.type][subtype].get("id") if kwargs[self.type].get(subtype) else ""
                self.data = LinkTo.create(page=sub_id)
                if self.plain_text == "Untitled":
                    self.plain_text = repr(self.data)
                else:
                    self.plain_text = "LinkTo(" + self.plain_text + ")"
                self.simple = self.data.link
            elif subtype == "database":
                sub_id = kwargs[self.type][subtype].get("id") if kwargs[self.type].get(subtype) else ""
                self.data = LinkTo.create(database_id=sub_id)
                if self.plain_text == "Untitled":
                    self.plain_text = repr(self.data)
                else:
                    self.plain_text = "LinkTo(" + self.plain_text + ")"
                self.simple = self.data.link
            elif subtype == "date":
                self.data = {
                    "start": Model.format_iso_time(kwargs[self.type][subtype].get("start")),
                    "end": Model.format_iso_time(kwargs[self.type][subtype].get("end"))
                }
                self.simple = str(self.plain_text)
            elif subtype == "link_preview":
                self.simple = str(self.plain_text)
                self.plain_text = f"<{self.plain_text}>"
                self.data: Dict = kwargs[self.type]
        else:
            self.data: Dict = kwargs[self.type]
            self.simple = str(self.plain_text)

    def __str__(self):
        return str(self.plain_text)

    def __repr__(self):
        return f"RichText({self.plain_text})"

    def __bool__(self):
        return bool(self.plain_text)

    def _create_default_annotations(self):
        self.annotations = {
            "bold": False, "italic": False, "strikethrough": False,
            "underline": False, "code": False, "color": "default"
        }

    # def __len__(self):
    #     return len(self.plain_text)

    def get(self) -> Dict[str, Any]:
        """
        Text type supported only
        """
        return {
            "type": "text",
            "text": {"content": self.plain_text, "link": None},
            # "annotations": self.annotations,
            # "plain_text": self.plain_text,
        }


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
        return "".join(str(rt) for rt in self)

    def __repr__(self):
        return f"RichTextArray({str(self)})"

    def __bool__(self):
        return any(map(bool, self.array))

    def __add__(self, another: Union[RichTextArray, str]):
        if isinstance(another, str):
            another = RichTextArray.create(another)
        self.array.extend(another)
        return self

    def get(self) -> List[Dict[str, Any]]:
        return [item.get() for item in self]

    @classmethod
    def create(cls, text: str):
        return cls([{"type": "text", "plain_text": text, "text": {}}])

    @property
    def simple(self) -> str:
        return "".join(rt.simple for rt in self)


class User(object):
    """
    The User object represents a user in a Notion workspace.
    """
    path = "users"

    def __init__(self, **kwargs) -> None:
        """
        Create an User object by providing dict from API.

        API attrs (from API docs):
        Mandatory:
        :param id: str
        :param object: str

        Optional:
        :param type: str
        :param name: str
        :param avatar_url: str

        Also Local attrs:
        :param raw: dict from API
        :param email: str if user is person
        """
        self.id = kwargs.get("id", "").replace("-", "")
        self.object = kwargs.get("object")  # user
        self.type = kwargs.get("type")
        self.name = kwargs.get("name")
        self.avatar_url = kwargs.get("avatar_url")
        if self.type == "person" and kwargs.get(self.type):
            self.email = kwargs[self.type].get("email")
        else:
            self.email = None
        self.raw = kwargs

    def __str__(self):
        if self.name and self.email:
            name = f"{self.name}({self.email})"
        else:
            name = self.name
        return name if name else self.id

    def __repr__(self):
        return f"User({self})"

    def get(self) -> Dict[str, str]:
        return {
            "object": self.object,
            "id": self.id
        }

    @classmethod
    def create(cls, id: str):
        return cls(object="user", id=id)


class Model(object):
    """
    :param id:
    :param object:
    :param created_time:
    :param last_edited_time:
    :param created_by:
    :param last_edited_by:
    :param raw:
    """

    def __init__(self, **kwargs) -> None:
        self.id = kwargs.get("id", "").replace("-", "")
        self.object = kwargs.get("object")
        self.created_time = self.format_iso_time(kwargs.get("created_time"))
        self.last_edited_time = self.format_iso_time(kwargs.get("last_edited_time"))
        self.created_by = User(**kwargs["created_by"]) if kwargs.get("created_by") else None
        self.last_edited_by = User(**kwargs["last_edited_by"]) if kwargs.get("last_edited_by") else None
        self.raw = kwargs

    @classmethod
    def format_iso_time(cls, time: str) -> Optional[datetime]:
        if not time:
            return None
        return datetime.fromisoformat(time.replace("Z", "+00:00"))


class Property(object):
    def __init__(self, data: Dict[str, str]):
        self.to_delete = True if data.get("type") is None else False
        self.id: str = data.get("id")
        self.type: str = data.get("type", "")
        self.name: str = data.get("name")
        self.raw = data

    def __str__(self):
        return self.name if self.name else self.type

    def __repr__(self):
        return f"Property({self})"

    def get(self) -> Optional[Dict[str, Dict]]:
        # property removing while patch
        if self.to_delete:
            return None
        # property renaming while patch
        data = {}
        if self.name:
            data["name"] = self.name
        # property retyping while patch
        if self.type:
            data[self.type] = {}
        return data

    @classmethod
    def create(cls, type_: Optional[str] = "", **kwargs):
        """
        Property Schema Object (watch docs)

        + addons:
        set type = `None` to delete this Property
        set param `name` to rename this Property
        """
        return cls({"type": type_, **kwargs})


class PropertyValue(Property):
    def __init__(self, data: Dict, name: str, **kwargs):
        super().__init__(data)
        # getting Paginated Properties (for retrieving property item)
        # *Pagination
        if data.get("object") and data["object"] == "list":
            if data.get("results"):
                self.type = data["results"][0].get("type")
                data[self.type] = [sub_dict.get(sub_dict.get("type")) for sub_dict in data["results"]]

        self.name = name
        self.value = None

        if self.type in ["title", "rich_text"]:
            if isinstance(data[self.type], list):
                self.value = RichTextArray(data[self.type])
            elif isinstance(data[self.type], RichTextArray):
                self.value = data[self.type]
            else:
                self.value = RichTextArray.create(data[self.type])

        if self.type == "number":
            self.value: Optional[int, float] = data["number"]

        if self.type == "select":
            if data["select"] and isinstance(data["select"], dict):
                self.value: Optional[str] = data["select"].get("name")
            elif data["select"] and isinstance(data["select"], str):
                self.value = data["select"]
            else:
                self.value = None

        if self.type == "multi_select":
            self.value: List[str] = [(v.get("name") if isinstance(v, dict) else v) for v in data["multi_select"]]

        if self.type == "checkbox":
            self.value: bool = data["checkbox"]

        if self.type == "date":
            if isinstance(data["date"], datetime):
                self.value = data["date"].isoformat()
                self.start = data["date"]
                self.end = None
            elif data["date"]:
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
            self.value = User(**data.get(self.type))

        if self.type == "last_edited_by":
            self.value = User(**data.get(self.type))

        if self.type == "people":
            self.value = [user if isinstance(user, User) else User(**user) for user in data[self.type]]

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
                if data["rollup"]["date"]:
                    self.value: Optional[str] = data["rollup"]["date"].get("start")
                    self.start: Optional[datetime] = Model.format_iso_time(data["rollup"]["date"].get("start"))
                    self.end: Optional[datetime] = Model.format_iso_time(data["rollup"]["date"].get("end"))
                else:
                    self.value = None
                    self.start = None
                    self.end = None
            else:
                self.value = "unsupported rollup type"

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

    def get(self):
        # checkbox can not be `None`
        if self.type in ["checkbox"]:
            return {self.type: self.value}

        # empty values
        if not self.value:
            if self.type in ["multi_select", "relation", "rich_text", "people", "files"]:
                return {self.type: []}
            return {self.type: None}

        # RichTextArray
        if self.type in ["title", "rich_text"] and hasattr(self.value, "get"):
            return {self.type: self.value.get()}

        # simple values
        if self.type in ["number", "url", "email", "phone_number"]:
            return {self.type: self.value}

        # select type
        if self.type == "select":
            return {self.type: {"name": self.value}}

        # multi-select type
        if self.type == "multi_select":
            return {self.type: [{"name": tag} for tag in self.value]}

        # date type
        if self.type == "date" and hasattr(self, "start") and hasattr(self, "end"):
            with_time = True if self.start.hour or self.start.minute else False
            if self.start:
                start = self.start.astimezone().isoformat() if with_time else str(self.start.date())
            else:
                start = None
            if self.end:
                end = self.end.astimezone().isoformat() if with_time else str(self.end.date())
            else:
                end = None
            return {self.type: {"start": start, "end": end}}

        # people type
        if self.type == "people":
            return {self.type: [user.get() for user in self.value]}

        # unsupported types:
        if self.type in ["files", "relation"]:
            return {self.type: []}
        if self.type in ["created_time", "last_edited_by", "last_edited_time", "created_by"]:
            return None
        if self.type in ["formula", "rollup"]:
            return {self.type: {}}
        return None

    @classmethod
    def create(cls, type_: str = "", value: Any = None, **kwargs):
        """
        Property Value Object (watch docs)

        + addons:
        set type = `None` to delete this Property
        set param `name` to rename this Property
        """
        return cls({"type": type_, type_: value, **kwargs}, name="")


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
        self.title = (kwargs.get("title")
                      if isinstance(kwargs["title"], RichTextArray) or not kwargs.get("title")
                      else RichTextArray(kwargs["title"])
                      )
        self.properties = {
            name: (value if isinstance(value, Property) else Property(value))
            for name, value in kwargs["properties"].items()
        }
        self.parent = kwargs["parent"] if isinstance(kwargs.get("parent"), LinkTo) else LinkTo(**kwargs["parent"])
        self.url: str = kwargs.get("url")

    def __str__(self):
        return str(self.title)

    def __repr__(self):
        return f"Database({self.title})"

    def get(self) -> Dict[str, Dict]:
        new_dict = {
            "parent": self.parent.get(),
            "properties": {name: value.get() for name, value in self.properties.items()}
        }
        if isinstance(self.title, RichTextArray):
            new_dict["title"] = self.title.get()
        return new_dict

    @classmethod
    def create(cls, parent: LinkTo, properties: Dict[str, Property], title: Optional[RichTextArray] = None, **kwargs):
        return cls(parent=parent, properties=properties, title=title, **kwargs)


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
        self.parent = kwargs["parent"] if isinstance(kwargs.get("parent"), LinkTo) else LinkTo(**kwargs["parent"])
        self.archived: bool = kwargs.get("archived")
        self.url: str = kwargs.get("url")
        self.children = kwargs["children"] if "children" in kwargs else LinkTo(block=self)
        self.properties = {
            name: (PropertyValue(data, name) if not isinstance(data, PropertyValue) else data)
            for name, data in kwargs["properties"].items()
        }
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

    def get(self):
        new_dict = {
            "parent": self.parent.get(without_type=True),
            "icon": self.icon,  # optional
            "cover": self.cover,  # optional
            "properties": {name: p.get() for name, p in self.properties.items()},
        }
        if getattr(self, "children", None):
            new_dict["children"] = self.children.get()  # can not be None
        return new_dict

    @classmethod
    def create(
            cls, parent: LinkTo, properties: Optional[Dict[str, PropertyValue]] = None,
            title: Optional[RichTextArray, str] = None, children: Optional[BlockArray] = None, **kwargs
    ):
        if not properties:
            properties = {}
        if title:
            properties["title"] = PropertyValue.create("title", title)
        return cls(parent=parent, properties=properties, children=children, **kwargs)


class Block(Model):
    object = "block"
    path = "blocks"

    def __init__(self, **kwargs):
        """
        params from Model +
        :param has_children:
        :param type:
        :param archived:
        :param create_mode:
        """
        super().__init__(**kwargs)
        self.type: str = kwargs.get("type")
        self.has_children: bool = kwargs.get("has_children")
        self.archived: bool = kwargs.get("archived")
        self.children = LinkTo(block=self)
        self._level = kwargs["level"] if kwargs.get("level") else 0
        self.create_mode: bool = kwargs["create_mode"] if "create_mode" in kwargs else False
        self.parent = None
        self._plain_text = ""

        if self.create_mode:
            self.text = kwargs[self.type]
            if "checked" in kwargs:
                self.checked = kwargs["checked"]
            if "language" in kwargs:
                self.language = kwargs["language"]
            if "caption" in kwargs:
                self.caption = kwargs["caption"]
                if isinstance(self.caption, str):
                    self.caption = RichTextArray.create(self.caption)
            return

        if self.type == "paragraph":
            self.text = RichTextArray(kwargs[self.type].get("rich_text"))
            self._plain_text = self.text.simple

        elif "heading" in self.type:
            indent = self.type.split("_")[-1]
            indent_num = int(indent) if indent.isdigit() else 0
            prefix = "#" * indent_num + " "
            r_text = RichTextArray(kwargs[self.type].get("rich_text"))
            self.text = RichTextArray.create(prefix) + r_text
            self._plain_text = r_text.simple

        elif self.type == "callout":
            self.text = RichTextArray(kwargs[self.type].get("rich_text"))
            self._plain_text = self.text.simple
            self.icon: Dict = kwargs[self.type].get("icon")

        elif self.type == "quote":
            r_text = RichTextArray(kwargs[self.type].get("rich_text"))
            self.text = RichTextArray.create("| ") + r_text
            self._plain_text = r_text.simple

        elif "list_item" in self.type:
            r_text = RichTextArray(kwargs[self.type].get("rich_text"))
            self.text = RichTextArray.create("- ") + r_text
            self._plain_text = r_text.simple
            # Numbers does not support cause of lack of relativity

        elif self.type == "to_do":
            self.checked: bool = kwargs[self.type].get("checked")
            prefix = "[x] " if self.checked else "[ ] "
            r_text = RichTextArray(kwargs[self.type].get("rich_text"))
            self.text = RichTextArray.create(prefix) + r_text
            self._plain_text = r_text.simple

        elif self.type == "toggle":
            r_text = RichTextArray(kwargs[self.type].get("rich_text"))
            self.text = RichTextArray.create("> ") + r_text
            self._plain_text = r_text.simple

        elif self.type == "code":
            r_text = RichTextArray(kwargs[self.type].get("rich_text"))
            self.text = RichTextArray.create("```\n") + r_text + "\n```"
            self._plain_text = r_text.simple
            self.language: str = kwargs[self.type].get("language")
            self.caption = RichTextArray(kwargs[self.type].get("caption"))

        # when the block is child_page, parent will be the page object
        # when the block is child_database, parent AND children will be the database object
        elif "child" in self.type:
            self.text: str = kwargs[self.type].get("title")
            self._plain_text = str(self.text)
            if self.type == "child_page":
                # self.children is already set
                self.parent = LinkTo(type="page", page=self.id)
                self._plain_text = str(self.parent.link)
            elif self.type == "child_database":
                # well yes. parent and children are the same. parent of this database will be the page of this block
                # and the database is children of this block
                self.parent = LinkTo.create(database_id=self.id)
                self.children = LinkTo.create(database_id=self.id)
                self._plain_text = str(self.parent.link)
                if not self.text:
                    self.text = repr(self.children)
            # page self.has_children is correct. checked.
            # database self.has_children is false.
            # database with custom source had no title!

        # hello, markdown
        elif self.type == "embed":
            self.caption = RichTextArray(kwargs[self.type].get("caption"))
            text = kwargs[self.type].get("url")
            self._plain_text = str(text)
            if self.caption:
                self.text = f'[{self.caption}]({text})'
            else:
                self.text = f'<{text}>' if text else "*Empty embed*"

        elif self.type == "image":
            self.caption = RichTextArray(kwargs[self.type].get("caption"))
            subtype = kwargs[self.type].get("type")
            if subtype == "file":
                # The file S3 URL will be valid for 1 hour
                self.expiry_time = Model.format_iso_time(kwargs[self.type][subtype].get("expiry_time"))
            else:
                self.expiry_time = None
            if subtype in ("file", "external"):
                text = kwargs[self.type][subtype].get("url")
                self._plain_text = str(text)
                if self.caption:
                    self.text = f'[{self.caption}]({text})'
                else:
                    self.text = f'<{text}>'
            else:
                self.text = "*Unknown image type*"
                self._plain_text = "None"

        elif self.type == "video":
            self.caption = RichTextArray(kwargs[self.type].get("caption"))
            subtype = kwargs[self.type].get("type")
            if subtype == "file":
                self.expiry_time = Model.format_iso_time(kwargs[self.type][subtype].get("expiry_time"))
            else:
                self.expiry_time = None
            if subtype in ("file", "external"):
                text = kwargs[self.type][subtype].get("url")
                self._plain_text = str(text)
                if self.caption:
                    self.text = f'[{self.caption}]({text})'
                else:
                    self.text = f'<{text}>'
            else:
                self.text = "*Unknown video type*"
                self._plain_text = "None"

        elif self.type == "file":
            self.caption = RichTextArray(kwargs[self.type].get("caption"))
            subtype = kwargs[self.type].get("type")
            if subtype == "file":
                self.expiry_time = Model.format_iso_time(kwargs[self.type][subtype].get("expiry_time"))
            else:
                self.expiry_time = None
            if subtype in ("file", "external"):
                text = kwargs[self.type][subtype].get("url")
                self._plain_text = str(text)
                if self.caption:
                    self.text = f'[{self.caption}]({text})'
                else:
                    self.text = f'<{text}>'
            else:
                self.text = "*Unknown file type*"
                self._plain_text = "None"

        elif self.type == "pdf":
            self.caption = RichTextArray(kwargs[self.type].get("caption"))
            subtype = kwargs[self.type].get("type")
            if subtype == "file":
                self.expiry_time = Model.format_iso_time(kwargs[self.type][subtype].get("expiry_time"))
            else:
                self.expiry_time = None
            if subtype in ("file", "external"):
                text = kwargs[self.type][subtype].get("url")
                self._plain_text = str(text)
                if self.caption:
                    self.text = f'[{self.caption}]({text})'
                else:
                    self.text = f'<{text}>'
            else:
                self.text = "*Unknown pdf type*"
                self._plain_text = "None"

        elif self.type == "breadcrumb":
            self.text = "*breadcrumb block*"
            self._plain_text = "None"

        elif self.type == "bookmark":
            self.caption = RichTextArray(kwargs[self.type].get("caption"))
            text = kwargs[self.type].get("url")
            self._plain_text = str(text)
            if self.caption:
                self.text = f'[{self.caption}]({text})'
            else:
                self.text = f'<{text}>' if text else "*Empty bookmark*"

        elif self.type == "link_preview":
            text = kwargs[self.type].get("url")
            self._plain_text = str(text)
            self.text = f'<{text}>'

        elif self.type == "link_to_page":
            self.link = LinkTo(**kwargs[self.type])
            self.text = repr(self.link)
            self._plain_text = str(self.link.link)

        elif self.type == "equation":
            self.text: str = kwargs[self.type].get("expression")
            self._plain_text = str(self.text)

        elif self.type == "divider":
            self.text = "---"
            self._plain_text = "None"

        elif self.type == "table_of_contents":
            self.text = "*Table of contents*"
            self._plain_text = "None"

        elif self.type == "template":
            r_text = RichTextArray(kwargs[self.type].get("rich_text"))
            self.text = RichTextArray.create("Template: ") + r_text
            self._plain_text = r_text.simple

        elif self.type == "synced_block":
            synced_from = kwargs[self.type].get("synced_from")
            self.text = "*SYNCED BLOCK:*"
            self._plain_text = "None"
            self.synced_from = LinkTo(**synced_from) if synced_from else None

        elif self.type == "table":
            self.table_width: int = kwargs[self.type].get("table_width")
            self.text = f"*Table {self.table_width}xN:*"
            self._plain_text = "None"

        elif self.type == "table_row":
            cells = kwargs[self.type].get("cells")
            self.text = RichTextArray.create("| ")
            for cell in cells:
                text_cell = RichTextArray(cell)
                self._plain_text += f"\"{text_cell}\","
                self.text += text_cell + " | "
            self._plain_text = self._plain_text.strip(",")

        elif self.type == "unsupported":
            self.text = "*****"
            self._plain_text = "None"

        else:
            self.text = "*UNKNOWN_BLOCK_TYPE*"
            self._plain_text = "None"

    def __str__(self):
        return str(self.text)

    def __repr__(self):
        return f"Block({str(self.text)[:30]})"

    def get(self, with_object_type: bool = False):
        if self.type in [
            "paragraph", "quote", "heading_1", "heading_2", "heading_3", "to_do",
            "bulleted_list_item", "numbered_list_item", "toggle", "callout", "code", "child_database"
        ]:

            text = RichTextArray.create(self.text) if isinstance(self.text, str) else self.text
            new_dict = {self.type: {"rich_text": text.get()}}
            if self.type == "to_do" and hasattr(self, "checked"):
                new_dict[self.type]["checked"] = self.checked
            if self.type == "code":
                new_dict[self.type]["language"] = getattr(self, "language", "plain text")
                if hasattr(self, "caption"):
                    new_dict[self.type]["caption"] = self.caption.get()
            if self.type == "child_database":
                new_dict = {self.type: {"title": str(text)}}
            if with_object_type:
                new_dict["object"] = "block"
                new_dict["type"] = self.type
            return new_dict
        return None

    @property
    def simple(self) -> str:
        if self._plain_text:
            return self._plain_text if self._plain_text != "None" else ""
        if getattr(self, "text", None):
            return str(self.text)
        return self._plain_text

    @classmethod
    def create(cls, text: str, type_: str = "paragraph", **kwargs):
        """
        :param text:   Block content
        :param type_:  Block types (API)
        :param kwargs:
            :kwargs param checked:  bool for to_do
            :kwargs param language: str for code
            :kwargs param caption:  str or RichTextArray for code
        :return:
        """
        new_dict = {
            "type": type_,
            type_: text,
        }
        return cls(**new_dict, create_mode=True, **kwargs)


class ElementArray(MutableSequence):
    class_map = {"page": Page, "database": Database, "block": Block}

    def __init__(self, array, create: bool = False):
        if create:
            self.array = array
            return

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

    def get(self):
        return [b.get() for b in self]

    @property
    def simple(self) -> str:
        return "\n".join(b._level * "\t" + b.simple for b in self)


class PageArray(ElementArray):
    def __repr__(self):
        r = str(self)[:30].replace("\n", " ")
        return f"PageArray({r})"


class LinkTo(object):
    """
    schema
    .type = `element_type`
    .id = `elementID`

    .get() - return API like style
    .create() - create in format `(page_id="123412341234")` or (database_id="13412341234")`
    """

    def __init__(
            self, block: Optional[Model] = None, from_object: Optional[Block, Page, Database] = None, **kwargs
    ):
        """
        Creates LinkTo object from API dict

        :param block: Block object can be provided instead other attrs. Internal usage.
        :param from_object: Any model object can be provided to create LinkTo to it.
        :param kwargs: API attrs. Internal usage.
        """
        if block:
            self.type = block.object
            self.id = block.id
            self.after_path = "children"
            self.uri = "blocks"
        # You can provide the object to create the LinkTo to it
        elif from_object:
            self.uri = from_object.path
            self.id = from_object.id
            if isinstance(from_object, Page):
                self.type = "page_id"
            elif isinstance(from_object, Database):
                self.type = "database_id"
            elif isinstance(from_object, Block):
                self.type = "block_id"
            elif isinstance(from_object, User):
                self.type = "user_id"
        else:
            self.type: str = kwargs.get("type")
            self.id: str = kwargs.get(self.type) if kwargs.get(self.type) else kwargs.get("id")
            if self.type == "workspace":
                self.id = ""
            self.after_path = ""
            if self.type == "page_id":
                self.uri = "blocks"
            elif self.type == "database_id":
                self.uri = "databases"
            # when type is set manually
            elif self.type == "page":
                self.uri = "pages"
            elif self.type == "block_id":
                self.uri = "blocks"
            elif self.type == "user_id":
                self.uri = "users"
            else:
                self.uri = None

        if isinstance(self.id, str):
            self.id = self.id.replace("-", "")

    def __str__(self):
        prefix = self.uri if self.uri else self.type
        if getattr(self, "after_path", ""):
            return f"{prefix}/{self.id}/{self.after_path}"
        return f"{prefix}/{self.id}"

    def __repr__(self):
        return f"LinkTo({self})"

    @property
    def link(self) -> str:
        return NOTION_URL + str(self)

    def get(self, without_type: bool = False):
        if self.type == "workspace":
            return {"type": "workspace", "workspace": True}
        if without_type:
            return {self.type: self.id}
        return {"type": self.type, self.type: self.id}

    @classmethod
    def create(cls, **kwargs):
        """
        `.create(page_id="123412341234")`
        `.create(database_id="13412341234")`
        `.create(workspace=True)`
        """
        for key, value in kwargs.items():
            return cls(type=key, id=value)
