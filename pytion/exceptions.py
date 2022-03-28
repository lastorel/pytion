# -*- coding: utf-8 -*-

import logging
import json
from typing import Dict

from requests import Response


logger = logging.getLogger(__name__)


class ClientError(Exception):
    def __init__(self, message: Response):
        req = message
        message = f"Failed with code {req.status_code}. Raw: {req.content}"
        super(ClientError, self).__init__(message)
        self.req = req
        self.request_body = req.request.body
        self.base = req.url
        self.error = message


class ServerError(Exception):
    def __init__(self, message: Response):
        req = message
        message = f"Failed with code {req.status_code}. Raw: {req.content}"
        super(ServerError, self).__init__(message)
        self.req = req
        self.request_body = req.request.body
        self.base = req.url
        self.error = message


class InvalidJSON(ClientError):
    def __init__(self, req: Response):
        message = f"Body could not be decoded as JSON: {req.request.body}"
        super(ClientError, self).__init__(message)


class InvalidRequestURL(ClientError):
    def __init__(self, req: Response):
        message = f"The request URL is not valid: {req.url}"
        super(ClientError, self).__init__(message)


class InvalidRequest(ClientError):
    def __init__(self, req: Response):
        message = f"This request is not supported: {req.url} {req.request.method}"
        super(ClientError, self).__init__(message)


class ValidationError(ClientError):
    def __init__(self, content: Dict):
        message = content.get("message")
        message = f"The request body does not match the schema: {message}"
        super(ClientError, self).__init__(message)


class MissingVersion(ClientError):
    pass


class Unauthorized(ClientError):
    pass


class RestrictedResource(ClientError):
    pass


class ObjectNotFound(ClientError):
    pass


class ConflictError(ClientError):
    pass


class RateLimited(ClientError):
    pass


class InternalServerError(ServerError):
    pass


class ServiceUnavailable(ServerError):
    pass


class DatabaseConnectionUnavailable(ServerError):
    pass


class ContentError(Exception):
    """Content Exception
    If the API URL does not point to a valid Notion API, the server may
    return a valid response code, but the content is not json. This
    exception is raised in those cases.
    """

    def __init__(self, message):
        req = message

        message = (
            "The server returned invalid (non-json) data. Maybe not a Notion server?"
        )

        super(ContentError, self).__init__(message)
        self.req = req
        self.request_body = req.request.body
        self.base = req.url
        self.error = message


def find_request_error(req: Response):
    try:
        content = req.json()
    except json.JSONDecodeError:
        logger.error(f"Result is not OK. JSON decoding fail\n{req.content}")
        raise ContentError(req)
    status_code = req.status_code
    error_code = content.get("code")
    if error_code:
        if error_code == "invalid_json":
            raise InvalidJSON(req)
        elif error_code == "invalid_request_url":
            raise InvalidRequestURL(req)
        elif error_code == "invalid_request":
            raise InvalidRequest(req)
        elif error_code == "validation_error":
            raise ValidationError(content)
        pass
# todo
    return content
