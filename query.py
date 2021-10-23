# -*- coding: utf-8 -*-

import json

import envs


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


class Request:
    def __init__(self, session, method=None, path=None, id_="", data=None, base=None, token=None, after_path=None):
        self.session = session
        self.base = base if base else envs.NOTION_URL
        self._token = token if token else envs.NOTION_SECRET
        self.version = envs.NOTION_VERSION
        self.auth = {"Authorization": "Bearer " + self._token}
        self.headers = {"Notion-Version": self.version, **self.auth}
        if method:
            self.result = self.method(method, path, id_, data, after_path)

    def method(self, method, path, id_="", data=None, after_path=None):
        url = self.base + path + "/" + id_
        if after_path:
            url += "/" + after_path
        result = self.session.request(method=method, url=url, headers=self.headers, json=data)
        if not result.ok:
            raise RequestError(result)
        try:
            return result.json()
        except json.JSONDecodeError:
            raise ContentError(result)
