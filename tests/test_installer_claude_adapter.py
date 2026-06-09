import pytest

from scripts.installer.adapters import adapter_names, get_adapter


def test_get_adapter_unknown_raises():
    with pytest.raises(KeyError):
        get_adapter("does-not-exist")


def test_claude_code_is_registered():
    assert "claude-code" in adapter_names()
