import requests
import pytest

import pytion.envs as envs
from pytion.exceptions import InvalidRequestURL, ContentError, ValidationError, ObjectNotFound


class TestRequest:
    def test_base(self, no):
        assert isinstance(no.session.session, requests.sessions.Session)
        assert no.session.session.verify is True
        assert no.session.base == envs.NOTION_URL
        assert no.session.version == envs.NOTION_VERSION
        assert "Notion-Version" in no.session.session.headers

    @pytest.mark.parametrize(
        "exec_method,exc",
        [
            ("post", InvalidRequestURL),
            ("PUT", InvalidRequestURL),
            ("delete", InvalidRequestURL),
            ("bla", ContentError),
        ],
    )
    def test_method__invalid_methods(self, no, exc, exec_method):
        with pytest.raises(exc):
            no.session.method(exec_method, "pages", id_="878d628488d94894ab14f9b872cd6870")

    def test_method__get(self, no):
        # reset cookies after bad requests
        no.session.session.cookies.clear()
        r = no.session.method("get", "pages", id_="878d628488d94894ab14f9b872cd6870")
        assert isinstance(r, dict)
        assert len(r) == 12
        assert r["object"] == "page"
        assert r["archived"] is False
        assert r["id"] == "878d6284-88d9-4894-ab14-f9b872cd6870"

    def test_method__patch_empty(self, no):
        r = no.session.method("patch", "pages", id_="878d628488d94894ab14f9b872cd6870")
        assert isinstance(r, dict)
        assert len(r) == 12
        assert r["object"] == "page"
        assert r["archived"] is False
        assert r["id"] == "878d6284-88d9-4894-ab14-f9b872cd6870"

    @pytest.mark.parametrize(
        "exec_path,exc",
        [
            ("page", InvalidRequestURL),
            ("DATABASE", InvalidRequestURL),
            ("", InvalidRequestURL),
            (None, TypeError),
        ],
    )
    def test_method__invalid_endpoints(self, no, exc, exec_path):
        with pytest.raises(exc):
            no.session.method("get", exec_path, id_="878d628488d94894ab14f9b872cd6870")

    @pytest.mark.parametrize(
        "id_,exc",
        [
            ("878d628488d94894ab14f9b872cd68709", ValidationError),
            ("878d6284-88d9-4894-ab14f9b872cd6870", ValidationError),
            ("878d628488d94894ab14f9b872cd687a", ObjectNotFound),
            ("", InvalidRequestURL),
            (None, TypeError),
        ],
    )
    def test_method__invalid_id(self, no, id_, exc):
        with pytest.raises(exc):
            no.session.method("get", "pages", id_=id_)
