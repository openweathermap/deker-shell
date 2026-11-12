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

"""The names available inside the shell.

This module's globals are the REPL globals: Deker's public API, ``np`` and ``datetime``,
the ``client`` of the session, the ``collections`` list, the ``collection`` chosen with ``use()``.
Nothing else leaks in here, so the completion offers only what makes sense in the shell.
"""

import datetime  # noqa: F401  # available in the REPL

import numpy as np  # noqa: F401  # available in the REPL

from deker import *  # noqa: F403  # the public Deker API is the point of the shell
from deker import Client, Collection

from deker_shell.help import help  # noqa: F401  # replaces the builtin inside the REPL

client: Client | None = None  # the client of the session, set by the shell start-up
collection: Collection | None = None  # the default collection, set by use()
collections: list[str] = []  # names of the collections, read at start-up


def use(name: str) -> None:
    """Get collection from client and save it to the ``collection`` variable.

    :param name: collection name
    :raises RuntimeError: if the shell has no client yet
    """
    global collection
    if client is None:
        raise RuntimeError("Deker client is not started")
    collection = client.get_collection(name)
    if not collection:
        print(f"Collection {name} doesn't exist")
    else:
        print(f"Saved {collection.name} to 'collection' variable")


def get_global_coll_variable() -> Collection | None:
    """Return the ``collection`` global variable.

    :returns: the collection chosen with ``use()``, or ``None`` if there is none yet
    """
    return collection
