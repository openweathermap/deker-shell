from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from prompt_toolkit.history import ThreadedHistory

from deker_shell import config
from deker_shell.completer import DekerCompleter
from deker_shell.config import configure
from deker_shell.history import BoundedFileHistory


@pytest.mark.usefixtures("restored_history_browser")
def test_configure_installs_the_custom_prompt(tmp_path: Path):
    repl = MagicMock(all_prompt_styles={})
    configure(repl, history_file=tmp_path / "history", history_size=10)
    prompt = repl.all_prompt_styles["custom"]
    assert prompt.in_prompt() == [("class:prompt", "> ")]
    assert prompt.in2_prompt(4) == [("class:prompt.dots", ". ")]
    assert prompt.out_prompt() == []
    assert repl.prompt_style == "custom"


@pytest.mark.usefixtures("restored_history_browser")
def test_configure_wires_completion_and_history(tmp_path: Path):
    repl = MagicMock(all_prompt_styles={})
    configure(repl, history_file=tmp_path / "history", history_size=10)
    assert isinstance(repl.completer, DekerCompleter)
    # the dictionary completion flag is read from the repl at every call, not copied once
    repl.enable_dictionary_completion = True
    assert repl.completer._python_completer.enable_dictionary_completion() is True
    repl.enable_dictionary_completion = False
    assert repl.completer._python_completer.enable_dictionary_completion() is False
    assert repl.enable_fuzzy_completion is True
    assert repl.enable_history_search is True
    # the same bounded history serves the input buffer and the F3 browser
    assert isinstance(repl.history, ThreadedHistory)
    assert repl.default_buffer.history is repl.history
    assert isinstance(repl.history.history, BoundedFileHistory)
    assert repl.history.history.max_entries == 10


def test_configure_switches_the_history_browser_to_the_selection_order(tmp_path: Path):
    repl = MagicMock(all_prompt_styles={})
    with patch.object(config, "insert_in_selection_order") as switch:
        configure(repl, history_file=tmp_path / "history", history_size=10)
    switch.assert_called_once_with()
