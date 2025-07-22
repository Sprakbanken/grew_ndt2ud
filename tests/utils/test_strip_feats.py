import pytest

from ndt2ud.utils import strip_feats


def test_strip_feats_removes_specified_keys():
    token_features = {
        "__RAW_MISC__": "misc",
        "textform": "foo",
        "wordform": "bar",
        "lemma": "baz",
        "upos": "NOUN",
    }
    result = strip_feats(token_features)
    assert "__RAW_MISC__" not in result
    assert "textform" not in result
    assert "wordform" not in result
    assert result == {"lemma": "baz", "upos": "NOUN"}


def test_strip_feats_does_not_modify_original():
    token_features = {
        "__RAW_MISC__": "misc",
        "textform": "foo",
        "wordform": "bar",
        "lemma": "baz",
    }
    original = token_features.copy()
    _ = strip_feats(token_features)
    assert token_features == original


def test_strip_feats_raises_keyerror_if_missing_keys():
    token_features = {"lemma": "baz"}
    with pytest.raises(KeyError):
        strip_feats(token_features)
