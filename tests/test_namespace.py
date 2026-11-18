from unittest.mock import MagicMock, patch

import pytest

from deker_shell import namespace
from deker_shell.namespace import get_global_coll_variable, use

PUBLIC_NAMES = {name for name in vars(namespace) if not name.startswith("_")}


def test_repl_sees_the_deker_api_and_the_shell_helpers_only():
    import deker

    assert set(deker.__all__) <= PUBLIC_NAMES
    assert {"np", "datetime", "help", "client", "collection", "collections", "use", "get_global_coll_variable"} <= (
        PUBLIC_NAMES
    )
    # nothing from the shell internals or its own imports
    assert PUBLIC_NAMES - set(deker.__all__) == {
        "np",
        "datetime",
        "help",
        "client",
        "collection",
        "collections",
        "use",
        "get_global_coll_variable",
    }


class TestUse:
    def test_use_requires_a_started_client(self):
        with patch.object(namespace, "client", None):
            with pytest.raises(RuntimeError, match="not started"):
                use("test")

    def test_use_saves_the_collection(self, capsys):
        found = MagicMock()
        found.name = "test"
        with patch.object(namespace, "client", MagicMock(get_collection=MagicMock(return_value=found))):
            with patch.object(namespace, "collection", None):
                use("test")
                assert get_global_coll_variable() is found
                assert vars(namespace)["collection"] is found  # the REPL sees the same variable
        assert capsys.readouterr().out == "Saved test to 'collection' variable\n"

    def test_use_reports_a_missing_collection(self, capsys):
        with patch.object(namespace, "client", MagicMock(get_collection=MagicMock(return_value=None))):
            with patch.object(namespace, "collection", None):
                use("missing")
                assert get_global_coll_variable() is None
        assert capsys.readouterr().out == "Collection missing doesn't exist\n"
