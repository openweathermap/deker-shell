from pathlib import Path
from unittest.mock import MagicMock

from prompt_toolkit.history import ThreadedHistory

from deker_shell.completer import DekerCompleter
from deker_shell.config import configure
from deker_shell.history import BoundedFileHistory


def test_configure_installs_the_custom_prompt(tmp_path: Path):
    repl = MagicMock(all_prompt_styles={})
    configure(repl, history_file=tmp_path / "history", history_size=10)
    prompt = repl.all_prompt_styles["custom"]
    assert prompt.in_prompt() == [("class:prompt", "> ")]
    assert prompt.in2_prompt(4) == [("class:prompt.dots", ". ")]
    assert prompt.out_prompt() == []
    assert repl.prompt_style == "custom"


def test_configure_wires_completion_and_history(tmp_path: Path):
    repl = MagicMock(all_prompt_styles={})
    configure(repl, history_file=tmp_path / "history", history_size=10)
    assert isinstance(repl.completer, DekerCompleter)
    assert repl.enable_fuzzy_completion is True
    assert repl.enable_history_search is True
    # the same bounded history serves the input buffer and the F3 browser
    assert isinstance(repl.history, ThreadedHistory)
    assert repl.default_buffer.history is repl.history
    assert isinstance(repl.history.history, BoundedFileHistory)
    assert repl.history.history.max_entries == 10
