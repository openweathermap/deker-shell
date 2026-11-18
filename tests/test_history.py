from pathlib import Path

import pytest

from prompt_toolkit.history import FileHistory

from deker_shell.consts import HISTORY_TRIM_SLACK
from deker_shell.history import BoundedFileHistory


def commands(path: Path) -> list[str]:
    """Read the file back with the stock prompt_toolkit parser, oldest first."""
    return list(reversed(list(FileHistory(path).load_history_strings())))


@pytest.fixture
def history_file(tmp_path: Path) -> Path:
    return tmp_path / "nested" / "history"


def test_file_and_its_directory_are_created_on_first_command(history_file: Path):
    history = BoundedFileHistory(history_file, max_entries=10)
    assert not history_file.exists()
    history.store_string("x = 1")
    assert commands(history_file) == ["x = 1"]


def test_limit_must_be_positive(history_file: Path):
    with pytest.raises(ValueError, match="positive"):
        BoundedFileHistory(history_file, max_entries=0)


def test_file_is_trimmed_once_the_slack_is_used_up(history_file: Path):
    history = BoundedFileHistory(history_file, max_entries=5)
    for i in range(5 + HISTORY_TRIM_SLACK):
        history.store_string(f"cmd {i}")
    assert len(commands(history_file)) == 5 + HISTORY_TRIM_SLACK  # not yet

    history.store_string("one more")
    assert commands(history_file) == [f"cmd {i}" for i in range(HISTORY_TRIM_SLACK + 1, HISTORY_TRIM_SLACK + 5)] + [
        "one more"
    ]


def test_multiline_commands_survive_trimming(history_file: Path):
    history = BoundedFileHistory(history_file, max_entries=2)
    history.store_string("def f():\n    return 1")
    for i in range(HISTORY_TRIM_SLACK + 1):
        history.store_string(f"f() + {i}")
    history.store_string("for x in y:\n    pass\n")  # the 103rd command: the file is rewritten
    assert commands(history_file) == [f"f() + {HISTORY_TRIM_SLACK}", "for x in y:\n    pass\n"]


def test_loading_trims_a_file_longer_than_the_limit(history_file: Path):
    big = BoundedFileHistory(history_file, max_entries=100)
    for i in range(20):
        big.store_string(f"cmd {i}")

    small = BoundedFileHistory(history_file, max_entries=3)
    assert list(small.load_history_strings()) == ["cmd 19", "cmd 18", "cmd 17"]
    assert commands(history_file) == ["cmd 17", "cmd 18", "cmd 19"]


def test_timestamps_are_kept_when_rewriting(history_file: Path):
    history = BoundedFileHistory(history_file, max_entries=1)
    for i in range(HISTORY_TRIM_SLACK + 2):
        history.store_string(f"cmd {i}")
    text = history_file.read_text()
    assert text.count("# ") == 1
    assert text.count("+cmd") == 1
    assert not history_file.with_name("history.tmp").exists()


def test_loading_a_missing_or_empty_file_gives_nothing(history_file: Path):
    assert list(BoundedFileHistory(history_file, max_entries=3).load_history_strings()) == []
    history_file.write_text("")
    assert list(BoundedFileHistory(history_file, max_entries=3).load_history_strings()) == []
