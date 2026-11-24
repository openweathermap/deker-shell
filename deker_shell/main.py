# deker-shell - interactive management shell for deker
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

import asyncio
import runpy
import sys

from ast import literal_eval
from functools import partial
from pathlib import Path
from typing import Any

import click as click

from click import ClickException, Context, UsageError
from deker import Client
from deker.errors import DekerClientError
from ptpython.repl import embed

from deker_shell import namespace
from deker_shell.config import configure
from deker_shell.consts import DEFAULT_HISTORY_FILE, DEFAULT_HISTORY_SIZE, help_start
from deker_shell.utils import validate_uri


def parse_extra_value(value: str) -> Any:
    """Turn a command line value into a Python literal when it is one.

    ``10`` -> ``10``, ``1.5`` -> ``1.5``, ``True`` -> ``True``, ``None`` -> ``None``; anything else stays a string.

    :param value: raw command line value
    :returns: the literal or the string itself
    """
    try:
        return literal_eval(value)
    except (ValueError, SyntaxError):
        return value


def parse_extra_args(args: list[str]) -> dict[str, Any]:
    """Turn the unknown command line options into keyword arguments of the Deker client.

    Every option needs a value: ``--timeout 10`` -> ``{"timeout": 10}``; dotted options are grouped:
    ``--httpx_conf.timeout 10 --httpx_conf.http2 True`` -> ``{"httpx_conf": {"timeout": 10, "http2": True}}``.

    :param args: the command line left after the known options were taken
    :returns: keyword arguments for the client
    :raises UsageError: if an option has no value or an argument is not an option
    """
    kwargs: dict[str, Any] = {}
    for i in range(0, len(args), 2):
        option = args[i]
        if not option.startswith("-"):
            raise UsageError(f"Got unexpected extra argument ({option})")
        if i + 1 == len(args):
            raise UsageError(f"Option '{option}' requires a value.")
        key = option.replace("-", "")
        value = parse_extra_value(args[i + 1])
        if "." in key:
            kwargs_key, inner_key = key.split(".", 1)
            kwargs.setdefault(kwargs_key, {})[inner_key] = value
        else:
            kwargs[key] = value
    return kwargs


async def interactive_shell(uri: str, history_file: Path, history_size: int, **kwargs: Any) -> None:
    r"""Coroutine that starts a Python REPL from which we can access the Deker interface.

    :param uri: uri to Deker storage
    :param history_file: where the command history is kept between sessions
    :param history_size: commands kept in the history file
    :param \**kwargs: Client parameters
    """
    client = Client(uri, **kwargs)
    namespace.client = client
    try:
        namespace.collections = [coll.name for coll in client]

        if client.is_closed:
            sys.exit("Client is closed")

        click.echo(help_start)
        await embed(
            globals=vars(namespace),
            return_asyncio_coroutine=True,
            patch_stdout=True,
            configure=partial(configure, history_file=history_file, history_size=history_size),
        )
    except EOFError:
        # Stop the loop when quitting the repl. (Ctrl-D press.)
        asyncio.get_running_loop().stop()
    finally:
        try:
            client.close()
            click.echo("Exiting Deker")
        except Exception:
            pass


@click.command(
    context_settings=dict(ignore_unknown_options=True, allow_extra_args=True),
    help="Start an interactive Deker shell at URI: a local storage (file://...) or a Deker server (http(s)://...). "
    "A path to a .py file runs that script instead. Unknown options are passed to the Deker client as they are, "
    "dotted ones are grouped: --httpx_conf.timeout 10 -> httpx_conf={'timeout': 10}.",
)
@click.argument("uri", required=True, type=str)
@click.option("-w", "--workers", type=int, help="Number of threads for Deker.")
@click.option(
    "-t",
    "--write-lock-timeout",
    type=int,
    help="An amount of seconds during which a parallel writing process waits for release of the locked file.",
)
@click.option(
    "-c",
    "--write-lock-check-interval",
    type=int,
    help="An amount of time (in seconds) during which a parallel writing process sleeps between checks for locks.",
)
@click.option("-l", "--loglevel", type=str, help="Level of Deker loggers.")
@click.option(
    "--debug",
    is_flag=True,
    help="The same as -l DEBUG: the DEBUG level of the Deker loggers and the full traceback of an error at the start.",
)
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
@click.option(
    "--history-file",
    type=click.Path(dir_okay=False, path_type=Path),
    default=DEFAULT_HISTORY_FILE,
    show_default=True,
    help="File keeping the command history between sessions.",
)
@click.option(
    "--history-size",
    type=click.IntRange(min=1),
    default=DEFAULT_HISTORY_SIZE,
    show_default=True,
    help="Commands kept in the history file, the oldest ones are dropped.",
)
@click.pass_context
def start(
    ctx: Context,
    uri: str,
    history_file: Path,
    history_size: int,
    workers: int | None = None,
    write_lock_timeout: int | None = None,
    write_lock_check_interval: int | None = None,
    loglevel: str | None = None,
    debug: bool = False,
    memory_limit: int | str | None = None,
) -> None:
    """Application entrypoint.

    :param ctx: click Context with extra parameters (kwargs)
    :param uri: uri to Deker storage
    :param history_file: file keeping the command history between sessions
    :param history_size: commands kept in the history file
    :param workers: number of threads for Deker
    :param write_lock_timeout: An amount of seconds during which a parallel writing process waits for release
      of the locked file
    :param write_lock_check_interval: An amount of time (in seconds) during which a parallel writing process sleeps
      between checks for locks
    :param loglevel: Level of Deker loggers
    :param debug: the same as ``loglevel="DEBUG"``; wins over ``loglevel``
    :param memory_limit: Limit of memory allocation per one array/subset in bytes or in human representation of
      kilobytes, megabytes or gigabytes, e.g. ``"100K"``, ``"512M"``, ``"4G"``. Human representations will be
      converted into bytes. If result is ``<= 0`` - total RAM + total swap is used

      .. note:: This parameter is used for early runtime break in case of potential memory overflow
    :raises ClickException: if the script file does not exist or the Deker client cannot be opened; the traceback
      of the client is shown only at ``-l DEBUG`` or ``--debug``
    :raises UsageError: if an unknown option stands before the uri
    """
    if uri.endswith(".py"):
        path = Path(uri)
        if not path.exists():
            raise ClickException("File does not exist")
        runpy.run_path(path_name=uri)
    else:
        if uri.startswith("-"):
            raise UsageError(f"Unknown option '{uri}' must come after URI, together with its value.")
        validate_uri(uri)
        if debug:
            loglevel = "DEBUG"

        # deker client default parameters
        kwargs: dict[str, Any] = {
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

        kwargs.update(parse_extra_args(ctx.args))

        try:
            asyncio.run(interactive_shell(uri, history_file, history_size, **kwargs))
        except DekerClientError as e:
            if str(kwargs.get("loglevel", "")).upper() == "DEBUG":
                raise  # the whole traceback is wanted
            raise ClickException(str(e)) from e


if __name__ == "__main__":
    start()
