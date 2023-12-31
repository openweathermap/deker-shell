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
from pathlib import Path

from typing import TYPE_CHECKING, Optional, Union, Any  # noqa: I101

import click as click
import numpy as np  # noqa F401
from click import Context, ClickException

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


async def interactive_shell(uri: str, **kwargs: Any) -> None:
    """Coroutine that starts a Python REPL from which we can access the Deker interface.

    :param uri: uri to Deker storage
    :param kwargs: Client parameters
    """
    global client
    try:
        client = Client(uri, **kwargs)
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

        click.echo(help_start)
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
                click.echo("Exiting Deker")
            except Exception:
                pass


@click.command(context_settings=dict(ignore_unknown_options=True, allow_extra_args=True))
@click.argument("uri", required=True, type=str)
@click.option("-w", "--workers", type=int, help="Number of threads for Deker.")
@click.option(
    "-t",
    "--write-lock-timeout",
    type=int,
    help="An amount of seconds " "during which a parallel writing process " "waits for release of the locked file.",
)
@click.option(
    "-c",
    "--write-lock-check-interval",
    type=int,
    help="An amount of time (in seconds) "
    "during which a parallel writing process "
    "sleeps between checks for locks.",
)
@click.option("-l", "--loglevel", type=str, help="Level of Deker loggers.")
@click.option(
    "-m",
    "--memory-limit",
    type=str,
    help="Limit of memory allocation per one array/subset in bytes "
    "or in human representation of kilobytes, megabytes or gigabytes,"
    " e.g. '100K', '512M', '4G'."
    " Human representations will be converted into bytes. "
    "If result is <= 0, total RAM + total swap is used.",
)
@click.pass_context
def start(
    ctx: Context,
    uri: str,
    workers: Optional[int] = None,
    write_lock_timeout: Optional[int] = None,
    write_lock_check_interval: Optional[int] = None,
    loglevel: Optional[str] = None,
    memory_limit: Optional[Union[int, str]] = None,
) -> None:
    """Application entrypoint.

    :param ctx: click Context with extra parameters (kwargs)
    :param uri: uri to Deker storage
    :param workers: number of threads for Deker
    :param write_lock_timeout: An amount of seconds during which a parallel writing process waits for release
      of the locked file
    :param write_lock_check_interval: An amount of time (in seconds) during which a parallel writing process sleeps
      between checks for locks
    :param loglevel: Level of Deker loggers
    :param memory_limit: Limit of memory allocation per one array/subset in bytes or in human representation of
      kilobytes, megabytes or gigabytes, e.g. ``"100K"``, ``"512M"``, ``"4G"``. Human representations will be
      converted into bytes. If result is ``<= 0`` - total RAM + total swap is used

      .. note:: This parameter is used for early runtime break in case of potential memory overflow
    """
    if uri.endswith(".py"):
        path = Path(uri)
        if not path.exists():
            raise ClickException("File does not exist")
        runpy.run_path(path_name=uri)
    else:
        validate_uri(uri)

        # deker client default parameters
        kwargs = {
            "workers": workers,
            "write_lock_timeout": write_lock_timeout,
            "write_lock_check_interval": write_lock_check_interval,
            "loglevel": loglevel,
            "memory_limit": memory_limit,
        }
        default_keys = tuple(kwargs.keys())
        for key in default_keys:
            if not kwargs.get(key):
                kwargs.pop(key, None)

        # extra parameters
        if ctx.args:
            for i in range(0, len(ctx.args), 2):
                key = ctx.args[i].replace("-", "")
                value = ctx.args[i + 1]
                if "." in ctx.args[i]:
                    kwargs_key, inner_key = key.split(".", 1)
                    kwargs[kwargs_key] = {}
                    kwargs[kwargs_key][inner_key] = value
                else:
                    kwargs[key] = value

        asyncio.run(interactive_shell(uri, **kwargs))


if __name__ == "__main__":
    start()
