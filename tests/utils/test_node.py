from ndt2ud.utils import Node


def test_Node_post_init_sets_attributes_from_feats():
    node = Node(name="test", node_id="10", feats={"foo": "bar", "baz": "qux"})
    assert hasattr(node, "foo")
    assert hasattr(node, "baz")
    assert node.foo == "bar"
    assert node.baz == "qux"
    assert node.feats["foo"] == "bar"
    assert node.feats["baz"] == "qux"


def test_Node_setattr_updates_feats():
    node = Node(name="test", node_id="11")
    node.newattr = "value"
    assert node.feats["newattr"] == "value"
    node.name = "changed"
    assert "name" not in node.feats  # name should not be in feats


def test_Node_repr_includes_feats():
    node = Node(name="n", node_id="1", feats={"A": "x", "B": "y"})
    rep = repr(node)
    assert rep.startswith("n [")
    assert "A=x" in rep
    assert "B=y" in rep


def test_Node_repr_and_feats_sync():
    node = Node(name="n", node_id="1", feats={"X": "1"})
    assert hasattr(node, "X")
    node.Y = "2"
    assert node.feats["Y"] == "2"
    r = repr(node)
    assert "n [" in r and "X=1" in r and "Y=2" in r
