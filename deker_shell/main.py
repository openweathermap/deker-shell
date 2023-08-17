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

import asyncio
import datetime  # noqa F401
import runpy
import sys

from typing import TYPE_CHECKING, Optional

import numpy as np  # noqa F401

from deker import *  # noqa F403
from ptpython.repl import embed

from deker_shell.config import configure
from deker_shell.consts import help_start
from deker_shell.help import help  # noqa F401
from deker_shell.utils import validate_uri


if TYPE_CHECKING:
    from deker import Client, Collection

collection: Optional[Collection] = None  # default collection variable, set by use("coll_name") method
client: Optional[Client] = None  # default variable for Client instance

async def interactive_shell(uri: str) -> None:
    """Coroutine that starts a Python REPL from which we can access the Deker interface.

    :param uri: client uri
    """
    global client
    try:
        client = Client(uri)
        collections: list[str] = [coll.name for coll in client]

        def use(name: str) -> None:
            """Get collection from client and saves it to collection variable.

            :param name: collection name
            """
            global collection
            collection = client.get_collection(name)  # type: ignore
            if not collection:
                print(f"Collection {name} doesn't exist")
            else:
                print(f"Saved {collection.name} to 'collection' variable")

        def get_global_coll_variable() -> Collection:
            """Return 'collection' global variable."""
            return globals()["collection"]

        if client.is_closed:
            sys.exit("Client is closed")

        print(help_start)
        await embed(  # type: ignore
            globals=globals(), locals=locals(), return_asyncio_coroutine=True, patch_stdout=True, configure=configure
        )
    except EOFError:
        # Stop the loop when quitting the repl. (Ctrl-D press.)
        asyncio.get_running_loop().stop()
    finally:
        if client is not None:
            try:
                client.close()
                print("Exiting Deker")
            except Exception:
                pass


def start() -> None:
    """Application entrypoint."""
    if len(sys.argv) < 2:
        print("No params passed")
    elif sys.argv[1].endswith(".py"):
        runpy.run_path(path_name=sys.argv[1])
    else:
        uri: str = sys.argv[1]
        validate_uri(uri)
        asyncio.run(interactive_shell(uri))


if __name__ == "__main__":
    start()
