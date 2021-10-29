# -*- coding: utf-8 -*-

import json
from urllib.parse import urlencode
from typing import Dict, Optional, Any, Union
from datetime import datetime

import requests

import pytion.envs as envs
from pytion.models import Property, PropertyValue


class RequestError(Exception):
    def __init__(self, message):
        req = message

        if req.status_code == 404:
            message = "The requested url: {} could not be found.".format(req.url)
        else:
            try:
                message = "The request failed with code {} {}: {}".format(
                    req.status_code, req.reason, req.json()
                )
            except ValueError:
                message = (
                    "The request failed with code {} {} but more specific "
                    "details were not returned in json.".format(
                        req.status_code, req.reason
                    )
                )

        super(RequestError, self).__init__(message)
        self.req = req
        self.request_body = req.request.body
        self.base = req.url
        self.error = req.text


class ContentError(Exception):
    """Content Exception
    If the API URL does not point to a valid Notion API, the server may
    return a valid response code, but the content is not json. This
    exception is raised in those cases.
    """

    def __init__(self, message):
        req = message

        message = (
            "The server returned invalid (non-json) data. Maybe not " "a Notion server?"
        )

        super(ContentError, self).__init__(message)
        self.req = req
        self.request_body = req.request.body
        self.base = req.url
        self.error = message


class Filter(object):
    _filter_condition_types = ["text", "number", "checkbox", "select", "multi_select", "date"]

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
            if property_obj.type in ["title", "rich_text", "url", "email", "phone"]:
                self.property_type = "text"
            elif "time" in property_obj.type:
                self.property_type = "date"
            else:
                self.property_type = property_obj.type
        else:
            self.property_type = property_type
            self.property_name = property_name

        if self.property_type not in self._filter_condition_types:
            raise ValueError(f"Allowed types {self.allowed_condition_types} ({property_type} is provided)")

        if self.property_type == "text":
            self.condition = "contains" if not condition else condition
            self.value = str(value)
        elif self.property_type == "number":
            self.condition = "equals" if not condition else condition
            self.value = int(value)
        elif self.property_type == "checkbox":
            self.condition = "equals" if not condition else condition
            self.value = bool(value)
        elif self.property_type == "select":
            self.condition = "equals" if not condition else condition
            self.value = str(value)
        elif self.property_type == "multi_select":
            self.condition = "contains" if not condition else condition
            self.value = str(value)
        elif self.property_type == "date":
            self.condition = "equals" if not condition else condition
            if isinstance(value, datetime):
                if not value.hour and not value.minute:
                    self.value = str(value.date())
                else:
                    self.value = value.isoformat()
            else:
                self.value = str(value)

        if property_obj and not value:
            self.value = getattr(property_obj, "value", None)
        if self.condition in [
            "is_empty", "is_not_empty", "past_week", "past_month", "past_year", "next_week", "next_month", "next_year"
        ]:
            self.value = True

        self.filter = {
            "property": self.property_name,
            self.property_type: {self.condition: self.value}
        }

    @property
    def allowed_condition_types(self):
        return ", ".join(self._filter_condition_types)

    def __repr__(self):
        if not getattr(self, "property_type"):
            return f"Filter({str(self.filter)})"
        return f"Filter({self.property_name} {self.condition} {self.value})"


class Sort(object):
    directions = ["ascending", "descending"]

    def __init__(self, property_name: str, direction: str):
        if direction not in self.directions:
            raise ValueError(f"Allowed types {self.directions} ({direction} is provided)")
        self.sorts = [{"property": property_name, "direction": direction}]

    def add(self, property_name: str, direction: str):
        if direction not in self.directions:
            raise ValueError(f"Allowed types {self.directions} ({direction} is provided)")
        self.sorts.append({"property": property_name, "direction": direction})

    def __repr__(self):
        r = [e.values() for e in self.sorts]
        return f"Sorts({r})"


class Request:
    def __init__(
            self,
            session: requests.Session,
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
        self.session = session
        self.base = base if base else envs.NOTION_URL
        self._token = token if token else envs.NOTION_SECRET
        self.version = envs.NOTION_VERSION
        self.auth = {"Authorization": "Bearer " + self._token}
        self.headers = {"Notion-Version": self.version, **self.auth}
        self.result = None
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
        if method:
            self.result = self.method(method, path, id_, data, after_path, limit)

    def method(self, method, path, id_="", data=None, after_path=None, limit=0):
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
        result = self.session.request(method=method, url=url, headers=self.headers, json=data)
        if not result.ok:
            raise RequestError(result)
        try:
            r = result.json()
        except json.JSONDecodeError:
            raise ContentError(result)
        if not limit:
            self.paginate(r, method, path, id_, data, after_path)
        return r

    def paginate(self, result, method, path, id_, data, after_path):
        if (result.get("has_more", False) is True) and (result.get("object", "") == "list"):
            next_start = result.get("next_cursor")

            # if GET method then parameters are in request string
            # if POST method then parameter are in body string
            if method == "get":
                if after_path:
                    after_path += "?" + urlencode({"start_cursor": next_start})
                else:
                    path += "?" + urlencode({"start_cursor": next_start})
            elif method == "post":
                if not data:
                    data = {}
                data.update({"start_cursor": next_start})
            while next_start:
                r = self.method(method, path, id_, data, after_path)
                if r.get("object", "") == "list" and r.get("results"):
                    result["results"].extend(r["results"])
                if r.get("has_more"):
                    next_start = r.get("next_cursor")
                else:
                    next_start = None

