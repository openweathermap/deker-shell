# deker-shell - interactive management shell for deker
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

from functools import partial
from pathlib import Path

from prompt_toolkit.formatted_text import AnyFormattedText
from prompt_toolkit.history import ThreadedHistory
from ptpython.prompt_style import PromptStyle
from ptpython.repl import PythonRepl

from deker_shell.completer import DekerCompleter
from deker_shell.history import BoundedFileHistory


class DekerPrompt(PromptStyle):
    """The prompt of the shell: ``> `` for a command, ``. `` for its continuation lines, nothing before the output."""

    def in_prompt(self) -> AnyFormattedText:
        """Prompt of a new command.

        :returns: the formatted prompt
        """
        return [("class:prompt", "> ")]

    def in2_prompt(self, width: int) -> AnyFormattedText:  # noqa: ARG002
        """Prompt of a continuation line of a command.

        :param width: width of the first prompt, unused: the dots are as short
        :returns: the formatted prompt
        """
        return [("class:prompt.dots", ". ")]

    def out_prompt(self) -> AnyFormattedText:
        """Prompt before the output of a command: none.

        :returns: an empty prompt
        """
        return []


def configure(repl: PythonRepl, history_file: Path, history_size: int) -> None:
    """Ptpython REPL config.

    https://github.com/prompt-toolkit/ptpython/blob/master/examples/python-embed-with-custom-prompt.py

    :param repl: ptpython repl
    :param history_file: where the command history is kept between sessions
    :param history_size: commands kept in the history file
    """
    repl.all_prompt_styles["custom"] = DekerPrompt()
    repl.prompt_style = "custom"
    repl.title = "Deker shell "
    repl.terminal_title = "Deker shell "
    repl.show_status_bar = False
    repl.confirm_exit = False
    repl.completer = DekerCompleter(
        repl.get_globals, repl.get_locals, partial(getattr, repl, "enable_dictionary_completion")
    )
    repl.enable_fuzzy_completion = True
    repl.enable_history_search = True

    # the buffer picks its history up lazily at the first prompt, so it can still be replaced here
    history = ThreadedHistory(BoundedFileHistory(history_file, history_size))
    repl.history = history
    repl.default_buffer.history = history

    repl.use_code_colorscheme("zenburn")
