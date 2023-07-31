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

from prompt_toolkit.formatted_text import AnyFormattedText
from ptpython.prompt_style import PromptStyle
from ptpython.repl import PythonRepl

from deker_shell.completer import get_repl_completer


def configure(repl: PythonRepl) -> None:
    """Ptpython REPL config.

    Ptpython version 3.0.23
    https://github.com/prompt-toolkit/ptpython/blob/master/examples/python-embed-with-custom-prompt.py

    :param repl: ptpyton repl
    """

    class CustomPrompt(PromptStyle):
        def in_prompt(self) -> AnyFormattedText:
            return [("class:prompt", ">")]

        def in2_prompt(self, width: int) -> AnyFormattedText:
            return [("class:prompt.dots", "...")]

        def out_prompt(self) -> AnyFormattedText:
            return []

    repl.all_prompt_styles["custom"] = CustomPrompt()
    repl.prompt_style = "custom"
    repl.title = "Deker shell "
    repl.terminal_title = "Deker shell "
    repl.show_status_bar = False
    repl.confirm_exit = False
    repl.completer = get_repl_completer(repl.get_globals, repl.get_locals, repl.enable_dictionary_completion)
    repl.use_code_colorscheme("zenburn")
