import requests
import pytest

import pytion.envs as envs
from pytion import InvalidRequestURL, ContentError, ValidationError, ObjectNotFound
from pytion.query import Sort
from pytion.models import Page


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

    @pytest.mark.parametrize(
        "data,exc",
        [
            ({"archived": False, "paragraph": ""}, ValidationError),
            ({"archived": False, "paragraph": {}}, ValidationError),
            ({"archived": False, "paragraph": None}, ValidationError),
            ({"archived": False, "paragraf": {}}, ValidationError),
            ({"archived": False, "synced_block": {}}, ValidationError),
        ],
        ids=("Empty string", "No rich_text paragraph", "None paragraph", "Wrong attribute name", "Wrong type")
    )
    def test_method__invalid_data(self, no, data, exc):
        block_id = "60c20e13d2ae4ccbb81b5f8f2c532319"
        with pytest.raises(exc):
            no.session.method("patch", path="blocks", id_=block_id, data=data)

    def test_method__after_path(self, no):
        page_id = "82ee5677402f44819a5da3302273400a"  # Page with some texts
        r = no.session.method("get", path="blocks", id_=page_id, after_path="children")
        assert isinstance(r, dict)
        assert r["object"] == "list"
        assert r["type"] == "block"
        assert r["block"] == {}
        assert len(r["results"]) == 3

    @pytest.mark.parametrize(
        "after_path,exc",
        [
            ("children", InvalidRequestURL),
            ("properties", InvalidRequestURL),
            ("None", InvalidRequestURL),
            ("query", InvalidRequestURL),
        ]
    )
    def test_method__invalid_after_path(self, no, after_path, exc):
        page_id = "82ee5677402f44819a5da3302273400a"  # Page with some texts
        with pytest.raises(exc):
            no.session.method("get", path="pages", id_=page_id, after_path=after_path)

    @pytest.mark.parametrize(
        "limit", (1, 10, 100, 101), ids=("1 page", "10 pages", "100 (max) pages", "101 (overmax) pages")
    )
    def test_method__limit_post(self, no, limit):  # no pagination expected
        db_id = "7d179e3dbe8e4bf0b605925eee98a194"  # Big Database
        r = no.session.method("post", path="databases", id_=db_id, after_path="query", data={}, limit=limit)
        assert isinstance(r, dict)
        assert r["object"] == "list"
        assert r["type"] == "page"
        if limit == 101:
            assert len(r["results"]) == 100  # no pagination when limit is set
        else:
            assert len(r["results"]) == limit
        assert r["has_more"] is True

    @pytest.mark.parametrize(
        "limit", (1, 10, 100, 101), ids=("1 page", "10 pages", "100 (max) pages", "101 (overmax) pages")
    )
    def test_method__limit_get(self, no, limit):
        page_id = "fb40b0c71ed54630ae03cbe12375c4b2"
        r = no.session.method("get", path="blocks", id_=page_id, after_path="children", limit=limit)
        assert isinstance(r, dict)
        assert r["object"] == "list"
        assert r["type"] == "block"
        if limit == 101:
            assert len(r["results"]) == 100  # no pagination when limit is set
        else:
            assert len(r["results"]) == limit
        assert r["has_more"] is True

    def test_method__limit_patch(self, no):  # limit in patch mode is ignored
        r = no.session.method("patch", "pages", id_="878d628488d94894ab14f9b872cd6870", limit=2)
        assert isinstance(r, dict)
        assert len(r) == 12
        assert r["object"] == "page"
        assert r["archived"] is False
        assert r["id"] == "878d6284-88d9-4894-ab14-f9b872cd6870"

    def test_method__invalid_limit(self, no):
        page_id = "82ee5677402f44819a5da3302273400a"  # Page with some texts
        with pytest.raises(ValidationError):
            no.session.method("get", path="blocks", id_=page_id, after_path="children", limit="query")

    def test_method__paginate(self, no):
        db_id = "7d179e3dbe8e4bf0b605925eee98a194"  # Big Database
        r = no.session.method("post", path="databases", id_=db_id, after_path="query", data={})
        assert isinstance(r, dict)
        assert r["object"] == "list"
        assert r["type"] == "page"
        assert len(r["results"]) == 201
        assert r["has_more"] is False
        assert r["next_cursor"] is None


class TestFilter:
    pass


class TestSort:
    def test_query__ascending(self, little_database):
        s = Sort("Digit", "ascending")
        r = little_database.db_query(sorts=s)
        assert isinstance(r.obj[0], Page)
        assert len(r.obj) == 4
        assert str(r.obj[0]) == "wait, what?"
        assert str(r.obj[1]) == "Parent testing page"
        assert "friends" in str(r.obj[2])
        assert bool(r.obj[3].title) is False

    def test_query__descending(self, little_database):
        s = Sort("Digit", "descending")
        r = little_database.db_query(sorts=s)
        assert isinstance(r.obj[0], Page)
        assert len(r.obj) == 4
        assert str(r.obj[2]) == "wait, what?"
        assert str(r.obj[1]) == "Parent testing page"
        assert "friends" in str(r.obj[0])
        assert bool(r.obj[3].title) is False

    def test_query__invalid_direction(self):
        with pytest.raises(ValueError):
            Sort("Digit", "reverse")

    def test_query__invalid_prop(self, little_database):
        s = Sort("Date", "descending")
        with pytest.raises(ValidationError):
            little_database.db_query(sorts=s)

    def test_query__timestamp(self, little_database):
        s = Sort("last_edited_time")
        r = little_database.db_query(sorts=s)
        assert isinstance(r.obj[0], Page)
        assert len(r.obj) == 4
        assert str(r.obj[0]) == "wait, what?"
        assert str(r.obj[2]) == "Parent testing page"
        assert "friends" in str(r.obj[1])
        assert bool(r.obj[3].title) is False
