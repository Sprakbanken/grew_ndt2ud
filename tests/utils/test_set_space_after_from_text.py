import pytest

from ndt2ud.utils import set_spaceafter_from_text


def test_set_spaceafter_from_text_basic():
    class DummyNode(dict):
        pass

    class DummyGraph(dict):
        def __init__(self, meta, nodes):
            super().__init__(nodes)
            self.meta = meta

    # "form" matches text, with spaces
    graph = DummyGraph(
        meta={"text": "A B", "sent_id": "1"},
        nodes={
            "1": DummyNode({"form": "A"}),
            "2": DummyNode({"form": "B"}),
        },
    )
    result = set_spaceafter_from_text(graph)
    assert "SpaceAfter" not in result["1"]
    assert "SpaceAfter" not in result["2"]


def test_set_spaceafter_from_text_no_spaceafter():
    class DummyNode(dict):
        pass

    class DummyGraph(dict):
        def __init__(self, meta, nodes):
            super().__init__(nodes)
            self.meta = meta

    # "form" matches text, but no space after first token
    graph = DummyGraph(
        meta={"text": "AB", "sent_id": "2"},
        nodes={
            "1": DummyNode({"form": "A"}),
            "2": DummyNode({"form": "B"}),
        },
    )
    result = set_spaceafter_from_text(graph)
    assert result["1"]["SpaceAfter"] == "No"


def test_set_spaceafter_from_text_raises_on_no_text():
    class DummyGraph(dict):
        def __init__(self, meta):
            self.meta = meta

    graph = DummyGraph(meta={"text": None, "sent_id": "x"})
    with pytest.raises(ValueError):
        set_spaceafter_from_text(graph)
