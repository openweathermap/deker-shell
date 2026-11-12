# deker-shell - interactive Python shell for deker
# Copyright (C) 2023  OpenWeather
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

import os

from collections.abc import Iterable
from pathlib import Path

from prompt_toolkit.history import FileHistory

from deker_shell.consts import HISTORY_TRIM_SLACK


class BoundedFileHistory(FileHistory):
    """Command history on disk that never holds more than ``max_entries`` commands.

    The file format is the one of ``prompt_toolkit.history.FileHistory``: one block per command,
    a ``# <timestamp>`` line followed by one ``+<line>`` per line of the command, blocks separated
    by a blank line. The file is rewritten with the newest ``max_entries`` blocks when it grows
    past ``max_entries + HISTORY_TRIM_SLACK`` commands and when it is loaded longer than the limit,
    so lowering the limit takes effect at the next start.

    :param filename: path to the history file; its directory is created if missing
    :param max_entries: commands to keep
    """

    def __init__(self, filename: Path, max_entries: int) -> None:
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
