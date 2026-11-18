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

from importlib.util import find_spec
from urllib.parse import urlparse

from click import ClickException

from deker_shell.consts import URI_SCHEME_ADAPTERS


def validate_uri(uri: str) -> None:
    """Validate uri: the scheme must be supported and the adapters serving it must be installed.

    :param uri: client uri
    :raises ClickException: if the scheme is unknown or its adapters package is missing
    """
    uri_scheme = urlparse(uri).scheme
    if uri_scheme not in URI_SCHEME_ADAPTERS:
        raise ClickException("Invalid uri")

    package, distribution = URI_SCHEME_ADAPTERS[uri_scheme]
    if find_spec(package) is None:
        raise ClickException(f"Deker adapters for '{uri_scheme}://' are not installed, run: pip install {distribution}")
