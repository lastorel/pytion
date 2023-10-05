# -*- coding: utf-8 -*-

import logging
from urllib.parse import urlencode
from typing import Dict, Optional, Any, Union
from datetime import datetime

import requests

import pytion.envs as envs
from pytion.models import Property, PropertyValue, User
from pytion.exceptions import find_response_error


logger = logging.getLogger(__name__)


class Filter(object):
    _filter_condition_types = [
        "rich_text", "number", "checkbox", "select", "multi_select", "date", "phone_number", "people", "title",
        "created_time", "last_edited_time", "phone_number", "status", "timestamp"
    ]

    def __init__(
            self,
            property_name: Optional[str] = None,
            value: Optional[Any] = None,
            property_type: Optional[str] = None,
            condition: Optional[str] = None,
            raw: Optional[Dict] = None,
            property_obj: Optional[Union[Property, PropertyValue]] = None,
            **kwargs,
    ):
        if raw:
            self.filter = raw
            return
        if property_obj:
            if property_obj.id:
                self.property_name = property_obj.id
            else:
                self.property_name = property_obj.name
            if property_obj.type in ["title", "rich_text", "url", "email"]:
                self.property_type = "rich_text"
            elif "time" in property_obj.type:
                self.property_type = "date"
            else:
                self.property_type = property_obj.type
        else:
            self.property_type = property_type
            self.property_name = property_name

        if self.property_type not in self._filter_condition_types:
            raise ValueError(f"Allowed types {self.allowed_condition_types} ({property_type} provided)")

        if self.property_type == "rich_text":
            self.condition = "contains" if not condition else condition
            self.value = str(value)
        elif self.property_type == "number":
            self.condition = "equals" if not condition else condition
            if "." in value:
                self.value = float(value)
            else:
                self.value = int(value)
        elif self.property_type == "checkbox":
            self.condition = "equals" if not condition else condition
            self.value = bool(value) if value else True
        elif self.property_type == "select":
            self.condition = "equals" if not condition else condition
            self.value = str(value)
        elif self.property_type == "multi_select":
            self.condition = "contains" if not condition else condition
            self.value = value[0] if isinstance(value, list) else str(value)
        elif self.property_type == "phone_number":
            self.condition = "contains" if not condition else condition
            self.value = str(value)
        elif self.property_type == "people":
            self.condition = "contains" if not condition else condition
            if isinstance(value, User):
                self.value = value.id
            else:
                self.value = str(value)
        elif self.property_type == "title":
            self.condition = "contains" if not condition else condition
            self.value = str(value)
        elif self.property_type == "date" or "_time" in self.property_type or self.property_type == "timestamp":
            self.condition = "equals" if not condition else condition
            if isinstance(value, datetime):
                if not value.hour and not value.minute:
                    self.value = str(value.date())
                else:
                    self.value = value.isoformat()
            else:
                self.value = str(value)
        elif self.property_type == "status":
            self.condition = "equals" if not condition else condition
            self.value = str(value)

        if property_obj and not value:
            self.value = getattr(property_obj, "value", None)
            if isinstance(self.value, list):
                self.value = self.value[0]
        if self.condition in ["is_empty", "is_not_empty"]:
            self.value = True
        elif self.condition in [
            "past_week", "past_month", "past_year", "next_week", "next_month", "next_year", "this_week"
        ]:
            self.value = {}
        self.filter = {
            "property": self.property_name,
            self.property_type: {self.condition: self.value}
        }
        # #70
        if "_time" in self.property_type:
            del self.filter["property"]
            self.filter["timestamp"] = self.property_type
        if self.property_type == "timestamp":
            del self.filter["property"]
            self.filter["timestamp"] = self.property_name  # created_time or last_edited_time
            self.filter[self.property_name] = {self.condition: self.value}

    @property
    def allowed_condition_types(self):
        return ", ".join(self._filter_condition_types)

    def __repr__(self):
        if not getattr(self, "property_type"):
            return f"Filter({str(self.filter)})"
        return f"Filter({self.property_name} {self.condition} {self.value})"


class Sort(object):
    directions = ["ascending", "descending"]

    def __init__(self, property_name: str, direction: str = "ascending"):
        """
        Sort object is used while querying database or search query:
        - self.sort object is used in search query (only single item supported by API)
        - self.sorts can contain multiple criteria and is used in database query
        """
        if direction not in self.directions:
            raise ValueError(f"Allowed types {self.directions} ({direction} is provided)")
        if property_name in ("created_time", "last_edited_time"):
            self.sort = {"timestamp": property_name, "direction": direction}
            self.sorts = [self.sort]
        else:
            self.sort = {"property": property_name, "direction": direction}
            self.sorts = [self.sort]

    def add(self, property_name: str, direction: str):
        if direction not in self.directions:
            raise ValueError(f"Allowed types {self.directions} ({direction} is provided)")
        self.sort = {"property": property_name, "direction": direction}
        self.sorts.append(self.sort)

    def __repr__(self):
        r = [e.values() for e in self.sorts]
        return f"Sorts({r})"


class Request(object):
    def __init__(
            self,
            api: object,  # Notion object
            method: Optional[str] = None,
            path: Optional[str] = None,
            id_: str = "",
            data: Optional[Dict] = None,
            base: Optional[str] = None,
            token: Optional[str] = None,
            after_path: Optional[str] = None,
            limit: int = 0,
            filter_: Optional[Filter] = None,
            sorts: Optional[Sort] = None,
    ):
        self.session = requests.Session()
        self.session.headers["accept"] = "application/json"
        self.base = base if base else envs.NOTION_URL
        self._token = token if token else envs.NOTION_SECRET
        if not self._token:
            logger.error("Token is not provided or file `token` is not found!")
        self.version = getattr(api, "version")
        self.auth = {"Authorization": "Bearer " + self._token}
        self.session.headers.update({"Notion-Version": self.version, **self.auth})
        self.result = None

        if method:
            self.result = self.method(method, path, id_, data, after_path, limit, filter_, sorts)

    def method(
            self, method: str, path: str, id_: str = "", data: Optional[Dict] = None,
            after_path: Optional[str] = None, limit: int = 0, filter_: Optional[Filter] = None,
            sorts: Optional[Sort] = None, pagination_loop: bool = False, sort: Optional[Sort] = None,
    ):
        if filter_:
            if data:
                data["filter"] = filter_.filter
            else:
                data = {"filter": filter_.filter}
        if sorts:
            if data:
                data["sorts"] = sorts.sorts
            else:
                data = {"sorts": sorts.sorts}
        if sort:  # specific attr in 'search' query. strange
            if data:
                data["sort"] = sort.sort
            else:
                data = {"sort": sort.sort}
        url = self.base + path + "/" + id_
        if limit and method == "get":
            if after_path:
                after_path += "?" + urlencode({"page_size": limit})
            else:
                path += "?" + urlencode({"page_size": limit})
        if limit and method == "post":
            if not data:
                data = {}
            data.update({"page_size": limit})
        if after_path:
            url += "/" + after_path
        logger.info(f"Request {method} {url}")
        logger.debug(f"METHOD: {method.upper()}")
        logger.debug(f"URL: {url}")
        logger.debug(f"DATA: {data}")
        result = self.session.request(method=method, url=url, json=data)
        logger.debug(f"STATUS CODE: {result.status_code}")
        logger.debug(f"CONTENT: {result.content}")
        logger.info(f"{result.status_code} Received")

        r = find_response_error(result)

        # pagination section
        if not limit and not pagination_loop:
            self.paginate(r, method, path, id_, data, after_path)

        return r

    def paginate(self, result, method, path, id_, data, after_path):
        if (result.get("has_more", False) is True) and (result.get("object", "") == "list"):
            next_start = result.get("next_cursor")
            logger.info(f"Paginated answer. Repeat with offset {next_start}")

            super_after_path = after_path
            super_path = path

            while next_start:
                # if GET method then parameters are in request string
                # if POST method then parameters are in body
                if method == "get":
                    if after_path:
                        super_after_path = after_path + "?" + urlencode({"start_cursor": next_start})
                    else:
                        super_path = path + "?" + urlencode({"start_cursor": next_start})
                elif method == "post":
                    if not data:
                        data = {}
                    data.update({"start_cursor": next_start})

                r = self.method(method, super_path, id_, data, super_after_path, pagination_loop=True)
                if r.get("object", "") == "list" and r.get("results"):
                    result["results"].extend(r["results"])
                if r.get("has_more"):
                    next_start = r.get("next_cursor")
                else:
                    next_start = None
                result["has_more"] = r.get("has_more")
                result["next_cursor"] = r.get("next_cursor")
