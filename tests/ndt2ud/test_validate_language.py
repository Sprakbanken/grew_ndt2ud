import argparse

import pytest

from ndt2ud import validate_language


def test_validate_language_accepts_nb():
    assert validate_language("nb") == "nb"


def test_validate_language_accepts_nn():
    assert validate_language("nn") == "nn"


@pytest.mark.parametrize("lang", ["en", "no", "bokmål", "", "NB", "NN", None])
def test_validate_language_rejects_invalid(lang):
    with pytest.raises(argparse.ArgumentTypeError):
        validate_language(lang)
