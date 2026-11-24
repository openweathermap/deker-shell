import builtins

from unittest.mock import patch

from deker_shell.consts import help_text
from deker_shell.help import help


def test_help_without_an_object_prints_the_shell_guide(capsys):
    help()
    assert capsys.readouterr().out == f"{help_text}\n"


def test_help_with_an_object_falls_back_to_the_builtin():
    with patch.object(builtins, "help") as builtin_help:
        help(dict)
    builtin_help.assert_called_once_with(dict)
