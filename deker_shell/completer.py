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

import re

from collections.abc import Callable, Iterable
from typing import Any

from prompt_toolkit.completion import CompleteEvent, Completer, Completion
from prompt_toolkit.document import Document
from ptpython.completer import PythonCompleter

from deker_shell.consts import PRESET_NAMES

# the cursor is inside ``use(``: an optional opening quote and the name typed so far
USE_CALL = re.compile(r"""\buse\(\s*(?P<quote>['"]?)(?P<prefix>[^'"()]*)$""")


class DekerCompleter(Completer):
    """The stock ptpython completer with Deker tweaks.

    Inside ``use(`` only the names of the existing collections (the ``collections`` variable of
    the session) are offered, quoted. Names starting with ``_`` and ``mro`` are hidden until the
    word being typed starts with ``_``. The shell presets (``client``, ``collections``...) come
    before other names of the same match quality. Everything else is ptpython's behaviour: jedi
    offers parameters in an argument position and names in a value position, functions are
    displayed with ``()`` and parameters with ``...``.
    """

    def __init__(
        self,
        get_globals: Callable[[], dict[str, Any]],
        get_locals: Callable[[], dict[str, Any]],
        enable_dictionary_completion: Callable[[], bool],
    ) -> None:
        """Build the stock completer this one wraps.

        :param get_globals: function returning the REPL globals
        :param get_locals: function returning the REPL locals
        :param enable_dictionary_completion: function returning the ptpython dictionary completion flag
        """
        self._get_globals = get_globals
        self._get_locals = get_locals
        self._python_completer = PythonCompleter(get_globals, get_locals, enable_dictionary_completion)

    def _collection_names(self) -> list[str] | None:
        """Names of the collections known to the session.

        :returns: the ``collections`` variable of the REPL, or ``None`` if there is no such list of strings
        """
        names = self._get_locals().get("collections", self._get_globals().get("collections"))
        if isinstance(names, list) and all(isinstance(name, str) for name in names):
            return names
        return None

    def _use_completions(self, document: Document) -> list[Completion] | None:
        """Collection names for the cursor inside ``use(``.

        :param document: user input
        :returns: quoted collection names starting with what is typed, or ``None`` when the cursor is
            not inside ``use(`` or the session has no ``collections`` list to offer
        """
        match = USE_CALL.search(document.text_before_cursor)
        if match is None:
            return None
        names = self._collection_names()
        if names is None:
            return None
        quote, prefix = match["quote"], match["prefix"]
        closing_present = bool(quote) and document.text_after_cursor.startswith(quote)
        completions = []
        for name in names:
            if not name.startswith(prefix):
                continue
            if not quote:
                text = f'"{name}"'
            elif closing_present:
                text = name
            else:
                text = f"{name}{quote}"
            completions.append(Completion(text, -len(prefix), display=name, display_meta="collection"))
        return completions

    def get_completions(self, document: Document, complete_event: CompleteEvent) -> Iterable[Completion]:
        """Yield prompt toolkit completions.

        :param document: user input
        :param complete_event: event that called the completer
        :yields: completions matching the current user input
        """
        use_completions = self._use_completions(document)
        if use_completions is not None:
            yield from use_completions
            return
        show_private = document.get_word_before_cursor().startswith("_")
        presets: list[Completion] = []
        others: list[Completion] = []
        for completion in self._python_completer.get_completions(document, complete_event):
            if not show_private and completion.text.startswith(("_", "mro")):
                continue
            (presets if completion.text in PRESET_NAMES else others).append(completion)
        yield from presets
        yield from others
