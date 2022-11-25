from pytion.models import *


class TestProperty:
    def test_create(self):
        p = Property.create(type_="multi_select", name="multiselected")
        p.get()
        assert p.id is None
        assert p.type == "multi_select"
        assert p.to_delete is False

    def test_create__to_rename(self):
        p = Property.create(name="renamed")
        p.get()
        assert p.id is None
        assert p.type == ""
        assert p.name == "renamed"
        assert p.to_delete is False

    def test_create__to_delete(self):
        p = Property.create(type_=None)
        p.get()
        assert p.id is None
        assert p.type is None
        assert p.to_delete is True

    def test_create__relation_single(self):
        p = Property.create("relation", single_property="878d628488d94894ab14f9b872cd6870")
        p.get()
        assert p.id is None
        assert p.type == "relation"
        assert p.to_delete is False
        assert isinstance(p.relation, LinkTo)
        assert p.relation.uri == "databases"
        assert p.subtype == "single_property"

    def test_create__relation_dual(self):
        p = Property.create("relation", dual_property="878d628488d94894ab14f9b872cd6870")
        p.get()
        assert p.id is None
        assert p.type == "relation"
        assert p.to_delete is False
        assert isinstance(p.relation, LinkTo)
        assert p.relation.uri == "databases"
        assert p.subtype == "dual_property"

    def test_create__status(self):
        p = Property.create("status")
        p_dict = p.get()
        assert p.id is None
        assert p.type == "status"
        assert p.to_delete is False
        assert isinstance(p.options, list)
        assert isinstance(p.groups, list)
        assert bool(p_dict["status"]) is False


class TestPropertyValue:
    def test_create__status(self):
        p = PropertyValue.create("status", value="Done")
        p_dict = p.get()
        assert p.id is None
        assert p.type == "status"
        assert p_dict["status"]["name"] == "Done"
