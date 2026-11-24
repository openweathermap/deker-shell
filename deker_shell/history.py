# deker-shell - interactive Python shell for deker
# Copyright (C) 2023-2026  Openweather Ltd.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""The command history of the shell: the file keeping it between the sessions and the browser of ptpython (F3).

ptpython keeps the chosen lines in a ``set`` and asks ``sorted()`` for their order in every place that
needs it: the preview on the right, the inserted text, the cursor synchronisation between the panes and
the removal of a line from the preview. So the lines are always inserted in the order of the history,
whatever the order they were chosen in. Here the set is replaced with one that remembers the order of
choosing, and ``sorted`` of the module with a function answering that order, so every place agrees.
"""

import os

from collections.abc import Iterable, Iterator
from pathlib import Path

from prompt_toolkit.document import Document
from prompt_toolkit.history import FileHistory, History
from ptpython import history_browser
from ptpython.history_browser import HistoryMapping, PythonHistory

from deker_shell.consts import HISTORY_TRIM_SLACK


class BoundedFileHistory(FileHistory):
    """Command history on disk that never holds more than ``max_entries`` commands.

    The file format is the one of ``prompt_toolkit.history.FileHistory``: one block per command,
    a ``# <timestamp>`` line followed by one ``+<line>`` per line of the command, blocks separated
    by a blank line. The file is rewritten with the newest ``max_entries`` blocks when it grows
    past ``max_entries + HISTORY_TRIM_SLACK`` commands and when it is loaded longer than the limit,
    so lowering the limit takes effect at the next start.
    """

    def __init__(self, filename: Path, max_entries: int) -> None:
        """BoundedFileHistory constructor: creates the directory of the file if it is missing.

        :param filename: path to the history file; its directory is created if missing
        :param max_entries: commands to keep
        :raises ValueError: if ``max_entries`` is not positive
        """
        if max_entries < 1:
            raise ValueError(f"max_entries must be positive, got {max_entries}")
        filename.parent.mkdir(parents=True, exist_ok=True)
        super().__init__(filename)
        self.path = filename
        self.max_entries = max_entries
        self._entries = 0

    def _read_blocks(self) -> list[str]:
        """Split the file into command blocks, oldest first.

        :returns: raw text of every block, each ending with a newline
        """
        if not self.path.exists():
            return []
        blocks: list[str] = []
        current: list[str] = []
        with open(self.path, "rb") as f:
            for line_bytes in f:
                line = line_bytes.decode("utf-8", errors="replace")
                if line.startswith(("#", "+")):
                    current.append(line)
                elif current:
                    blocks.append("".join(current))
                    current = []
        if current:
            blocks.append("".join(current))
        return blocks

    def _rewrite(self, blocks: list[str]) -> None:
        """Replace the file with the given blocks atomically.

        :param blocks: command blocks to keep, oldest first
        """
        tmp = self.path.with_name(self.path.name + ".tmp")
        with open(tmp, "wb") as f:
            for block in blocks:
                f.write(b"\n")
                f.write(block.encode("utf-8", errors="replace"))
        os.replace(tmp, self.path)

    def trim(self) -> None:
        """Drop the oldest commands beyond ``max_entries``."""
        blocks = self._read_blocks()
        if len(blocks) > self.max_entries:
            self._rewrite(blocks[-self.max_entries :])
        self._entries = min(len(blocks), self.max_entries)

    def load_history_strings(self) -> Iterable[str]:
        """Load the commands, newest first, trimming the file to the limit on the way.

        :returns: the commands kept in the file
        """
        self.trim()
        return super().load_history_strings()

    def store_string(self, string: str) -> None:
        """Append a command and trim the file once it holds ``HISTORY_TRIM_SLACK`` commands too many.

        :param string: the accepted command
        """
        super().store_string(string)
        self._entries += 1
        if self._entries > self.max_entries + HISTORY_TRIM_SLACK:
            self.trim()


class SelectedLines(set[int]):
    """Numbers of the chosen history lines, iterated in the order they were chosen.

    Only the methods the history browser of ptpython uses keep the order: ``add``, ``remove``, ``discard``,
    ``clear``, ``in``, ``len`` and the iteration.
    """

    def __init__(self) -> None:
        """SelectedLines constructor: an empty set."""
        super().__init__()
        self._order: dict[int, None] = {}

    def add(self, line: int) -> None:
        """Choose a line; a line chosen already keeps its place.

        :param line: number of the history line
        """
        if line not in self:
            super().add(line)
            self._order[line] = None

    def remove(self, line: int) -> None:
        """Unchoose a line.

        :param line: number of the history line
        :raises KeyError: if the line is not chosen
        """
        super().remove(line)
        del self._order[line]

    def discard(self, line: object) -> None:
        """Unchoose a line if it is chosen.

        :param line: number of the history line; anything else is not chosen and does nothing, as in ``set``
        """
        super().discard(line)
        if isinstance(line, int):
            self._order.pop(line, None)

    def clear(self) -> None:
        """Unchoose every line."""
        super().clear()
        self._order.clear()

    def __iter__(self) -> Iterator[int]:
        """Iterate the lines in the order they were chosen.

        :returns: iterator over the line numbers
        """
        return iter(self._order)


def in_selection_order(lines: Iterable[int]) -> list[int]:
    """Answer the lines as they come: the replacement of ``sorted`` in the history browser of ptpython.

    :param lines: chosen lines, iterated in the order they were chosen
    :returns: the lines in that order
    """
    return list(lines)


class OrderedHistoryMapping(HistoryMapping):
    """The mapping of the history browser keeping the chosen lines in the order they were chosen."""

    def __init__(self, history: PythonHistory, python_history: History, original_document: Document) -> None:
        """OrderedHistoryMapping constructor: the mapping of ptpython with a ``SelectedLines`` set.

        :param history: the history browser
        :param python_history: the command history
        :param original_document: the input the browser was opened from
        """
        super().__init__(history, python_history, original_document)
        self.selected_lines = SelectedLines()


def insert_in_selection_order() -> None:
    """Switch the history browser of ptpython to inserting the chosen lines in the order they were chosen.

    The browser builds its mapping and orders the chosen lines through the names of its own module, so the
    two names are replaced there; calling this twice changes nothing more.
    """
    module = vars(history_browser)
    module["HistoryMapping"] = OrderedHistoryMapping
    module["sorted"] = in_selection_order
