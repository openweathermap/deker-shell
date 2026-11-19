from pathlib import Path
from unittest.mock import MagicMock

import pytest

from prompt_toolkit.document import Document
from prompt_toolkit.history import FileHistory, InMemoryHistory
from ptpython import history_browser

from deker_shell.consts import HISTORY_TRIM_SLACK
from deker_shell.history import (
    BoundedFileHistory,
    OrderedHistoryMapping,
    SelectedLines,
    in_selection_order,
    insert_in_selection_order,
)


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


COMMANDS = [
    'va["20261117T1200",0,0].describe()',
    "from PIL import Image",
    "Image.MAX_IMAGE_PIXELS = None",
    'img = Image.fromarray(data.squeeze(), mode="L")',
    "import sys",
    "size = sys.getsizeof(data)",
]


def make_history() -> InMemoryHistory:
    history = InMemoryHistory()
    for command in COMMANDS:
        history.append_string(command)
    return history


class TestSelectedLines:
    def test_the_lines_come_in_the_order_they_were_added(self):
        lines = SelectedLines()
        for line in (4, 1, 2):
            lines.add(line)
        assert list(lines) == [4, 1, 2]
        assert len(lines) == 3
        assert 1 in lines
        assert 3 not in lines

    def test_a_line_added_twice_keeps_its_place(self):
        lines = SelectedLines()
        lines.add(4)
        lines.add(1)
        lines.add(4)
        assert list(lines) == [4, 1]
        assert len(lines) == 2

    def test_discard_takes_what_a_set_takes(self):
        lines = SelectedLines()
        lines.add(4)
        lines.discard("4")
        lines.discard(None)
        assert list(lines) == [4]

    def test_a_removed_line_added_again_goes_to_the_end(self):
        lines = SelectedLines()
        for line in (4, 1, 2):
            lines.add(line)
        lines.remove(4)
        assert list(lines) == [1, 2]
        lines.add(4)
        assert list(lines) == [1, 2, 4]

    def test_removing_a_line_that_is_not_chosen_raises(self):
        lines = SelectedLines()
        with pytest.raises(KeyError):
            lines.remove(7)
        assert list(lines) == []

    def test_discard_and_clear_keep_the_set_and_the_order_together(self):
        lines = SelectedLines()
        for line in (4, 1, 2):
            lines.add(line)
        lines.discard(1)
        lines.discard(9)
        assert list(lines) == [4, 2]
        assert 1 not in lines
        lines.clear()
        assert list(lines) == []
        assert len(lines) == 0


@pytest.mark.parametrize("lines", [[], [3], [4, 1, 2]])
def test_in_selection_order_keeps_the_order(lines):
    chosen = SelectedLines()
    for line in lines:
        chosen.add(line)
    assert in_selection_order(chosen) == lines


@pytest.mark.usefixtures("restored_history_browser")
class TestOrderedHistoryMapping:
    def test_the_chosen_lines_are_inserted_in_the_order_they_were_chosen(self):
        """import sys, then from PIL import Image, then Image.MAX_IMAGE_PIXELS = None: in that order."""
        insert_in_selection_order()
        mapping = OrderedHistoryMapping(MagicMock(), make_history(), Document(""))
        for line in (4, 1, 2):
            mapping.selected_lines.add(line)
        assert mapping.get_new_document().text == "import sys\nfrom PIL import Image\nImage.MAX_IMAGE_PIXELS = None"

    def test_the_chosen_lines_are_inserted_at_the_cursor_of_the_input(self):
        insert_in_selection_order()
        mapping = OrderedHistoryMapping(MagicMock(), make_history(), Document("before", cursor_position=6))
        for line in (2, 1):
            mapping.selected_lines.add(line)
        assert mapping.get_new_document().text == "before\nImage.MAX_IMAGE_PIXELS = None\nfrom PIL import Image"

    def test_the_plain_mapping_of_ptpython_orders_by_the_history(self):
        """The reason of the replacement: ptpython itself inserts the lines in the order of the history."""
        vars(history_browser).pop("sorted", None)  # the builtin, as before insert_in_selection_order()
        mapping = history_browser.HistoryMapping(MagicMock(), make_history(), Document(""))
        for line in (4, 1, 2):
            mapping.selected_lines.add(line)
        assert mapping.get_new_document().text == "from PIL import Image\nImage.MAX_IMAGE_PIXELS = None\nimport sys"


@pytest.mark.usefixtures("restored_history_browser")
class TestInsertInSelectionOrder:
    def test_the_browser_gets_the_ordered_mapping_and_the_order_function(self):
        insert_in_selection_order()
        assert history_browser.HistoryMapping is OrderedHistoryMapping
        assert vars(history_browser)["sorted"] is in_selection_order

    def test_calling_it_twice_changes_nothing_more(self):
        insert_in_selection_order()
        insert_in_selection_order()
        assert history_browser.HistoryMapping is OrderedHistoryMapping
        assert vars(history_browser)["sorted"] is in_selection_order

    def test_the_browser_builds_the_ordered_mapping(self):
        """The browser of ptpython takes the mapping by the name of its module, so it gets ours."""
        insert_in_selection_order()
        mapping = history_browser.HistoryMapping(MagicMock(), make_history(), Document(""))
        assert isinstance(mapping, OrderedHistoryMapping)
        assert isinstance(mapping.selected_lines, SelectedLines)
