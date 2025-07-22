import pytest

from ndt2ud.utils import Edge


def test_edge_repr_defaults():
    edge = Edge(source="1", target="2")
    assert repr(edge) == "e: 1 -[]-> 2"


def test_Edge_repr_shows_all_attributes():
    edge = Edge(source="1", target="2", label="rel", name="e1")
    assert repr(edge) == "e1: 1 -[rel]-> 2"


def test_edge_fields():
    edge = Edge(source="X", target="Y", label="obj")
    assert edge.source == "X"
    assert edge.target == "Y"
    assert edge.label == "obj"
    assert edge.name == "e"
