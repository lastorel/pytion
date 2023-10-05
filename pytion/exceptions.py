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
        Exception.__init__(self, message)


class InvalidRequestURL(ClientError):
    def __init__(self, req: Response):
        message = f"The request URL is not valid: {req.url}"
        Exception.__init__(self, message)


class InvalidRequest(ClientError):
    def __init__(self, req: Response):
        message = f"This request is not supported: {req.url} {req.request.method}"
        Exception.__init__(self, message)


class InvalidGrant(ClientError):
    def __init__(self, req: Response):
        message = (
            "The provided authorization grant or refresh token is invalid, expired, revoked, "
            "does not match the redirection URI used in the authorization request"
        )
        Exception.__init__(self, message)


class ValidationError(ClientError):
    def __init__(self, content: Dict):
        message = content.get("message")
        message = f"The request body does not match the schema: {message}"
        Exception.__init__(self, message)


class MissingVersion(ClientError):
    def __init__(self, *args):
        message = "The request is missing the required Notion-Version header."
        Exception.__init__(self, message)


class Unauthorized(ClientError):
    def __init__(self, *args):
        message = "The bearer token is not valid."
        Exception.__init__(self, message)


class RestrictedResource(ClientError):
    def __init__(self, *args):
        message = "Given the bearer token used, the client doesn't have permission to perform this operation."
        Exception.__init__(self, message)


class ObjectNotFound(ClientError):
    def __init__(self, req: Response):
        message = f"{req.url}" \
                  "The resource does not exist or the resource has not been shared with owner of the bearer token."
        Exception.__init__(self, message)


class ConflictError(ClientError):
    def __init__(self, *args):
        message = "The transaction could not be completed, potentially due to a data collision. Make sure the " \
                  "parameters are up to date and try again."
        Exception.__init__(self, message)


class RateLimited(ClientError):
    def __init__(self, *args):
        message = "This request exceeds the number of requests allowed. Slow down and try again."
        Exception.__init__(self, message)


class InternalServerError(ServerError):
    def __init__(self, req: Response):
        self.req = req
        self.request_body = req.request.body
        self.base = req.url
        self.error = req.content
        message = f"An unexpected error occurred. Reach out to Notion support. {req.status_code}: " \
                  f"{req.request.method} {self.base} {self.request_body} -> {self.error}"
        Exception.__init__(self, message)


class ServiceUnavailable(ServerError):
    def __init__(self, *args):
        message = "Notion is unavailable. Try again later."
        Exception.__init__(self, message)


class DatabaseConnectionUnavailable(ServerError):
    def __init__(self, *args):
        message = "Notion's database is unavailable or in an unqueryable state. Try again later."
        Exception.__init__(self, message)


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


def find_response_error(req: Response) -> Dict:
    try:
        content = req.json()
    except json.JSONDecodeError:
        logger.error(f"Result is not OK. JSON decoding fail\n{req.content}")
        raise ContentError(req)
    if req.ok:
        return content
    logger.error(f"Result is not OK. {req.status_code}\n{req.reason}")
    status_code = int(req.status_code)
    error_code = content.get("code")
    if error_code:
        if error_code == "invalid_json":
            raise InvalidJSON(req)
        elif error_code == "invalid_request_url":
            raise InvalidRequestURL(req)
        elif error_code == "invalid_request":
            raise InvalidRequest(req)
        elif error_code == "invalid_grant":
            raise InvalidGrant(req)
        elif error_code == "validation_error":
            raise ValidationError(content)
        elif error_code == "missing_version":
            raise MissingVersion()
        elif error_code == "unauthorized":
            raise Unauthorized()
        elif error_code == "restricted_resource":
            raise RestrictedResource()
        elif error_code == "object_not_found":
            raise ObjectNotFound(req)
        elif error_code == "conflict_error":
            raise ConflictError()
        elif error_code == "rate_limited":
            raise RateLimited()
        elif error_code == "internal_server_error":
            raise InternalServerError(req)
        elif error_code == "service_unavailable":
            raise ServiceUnavailable()
        elif error_code == "database_connection_unavailable":
            raise DatabaseConnectionUnavailable()
    if 400 <= status_code < 500:
        raise ClientError(req)
    elif 500 <= status_code < 600:
        raise ServerError(req)
    raise Exception(f"An unexpected error occurred. {req.status_code}: {req.content}")
