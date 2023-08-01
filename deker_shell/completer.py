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

from typing import Any, Callable, Dict, Iterable

from deker.types.private.shell import shell_completions
from prompt_toolkit.completion import CompleteEvent, Completer, Completion
from prompt_toolkit.document import Document
from ptpython.completer import PythonCompleter, _get_style_for_jedi_completion
from ptpython.utils import get_jedi_script_from_document


class JediCompleter(Completer):
    """Overrided ptpython jedi completer."""

    def __init__(
        self,
        get_globals: Callable[[], Dict[str, Any]],
        get_locals: Callable[[], Dict[str, Any]],
    ) -> None:
        super().__init__()

        self.get_globals = get_globals
        self.get_locals = get_locals

    def get_completions(self, document: Document, complete_event: CompleteEvent) -> Iterable[Completion]:
        """Yields prompt toolkit completions.

        :param document: user input
        :param complete_event: event that called the completer
        """
        script = get_jedi_script_from_document(document, self.get_locals(), self.get_globals())

        if script:
            try:
                jedi_completions = [
                    completion
                    for completion in script.complete(
                        column=document.cursor_position_col,
                        line=document.cursor_position_row + 1,
                    )
                    if not completion.name.startswith(("_", "__", "mro"))
                ]  # hide private and magic methods
            except Exception:
                # Supress all Jedi exceptions.
                pass
            else:
                # Move function parameters to the top.
                jedi_completions = sorted(
                    jedi_completions,
                    key=lambda jc: (
                        # Params first.
                        jc.type != "param",
                        # non builtins libs first
                        not jc.module_name.startswith("jedi"),
                        # Private at the end.
                        jc.name.startswith("_"),
                        # Then sort by name.
                        jc.name_with_symbols.lower(),
                    ),
                )
                for jc in jedi_completions:
                    if any(deker_obj in document.text for deker_obj in shell_completions) and jc.type != "param":
                        continue
                    if jc.type == "function":
                        suffix = "()"
                    else:
                        suffix = ""

                    if jc.type == "param":
                        suffix = "..."

                    yield Completion(
                        jc.name_with_symbols,
                        len(jc.complete) - len(jc.name_with_symbols),
                        display=jc.name_with_symbols + suffix,
                        display_meta=jc.type,
                        style=_get_style_for_jedi_completion(jc),
                    )


def get_repl_completer(
    get_globals: Callable, get_locals: Callable, enable_dictionary_completion: bool
) -> PythonCompleter:
    """Return repl completer with custom jedi completer.

    :param get_globals: function returning globals
    :param get_locals: function returning locals
    :param enable_dictionary_completion: repl flag
    """
    jedi_completer = JediCompleter(get_globals, get_locals)
    repl_completer = PythonCompleter(
        get_globals,
        get_locals,
        lambda: enable_dictionary_completion,
    )
    repl_completer._jedi_completer = jedi_completer  # type: ignore
    return repl_completer
