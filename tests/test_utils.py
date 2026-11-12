from unittest.mock import patch

import pytest

from click import ClickException

from deker_shell import utils
from deker_shell.utils import validate_uri


@pytest.mark.parametrize(
    "uri",
    [
        "file:///tmp/deker",
        "http://localhost:8000",
        "https://user:password@deker.example.com",
        "https://node1:8000,node2:8000",
    ],
)
def test_supported_schemes_pass_when_their_adapters_are_installed(uri):
    with patch.object(utils, "find_spec", return_value=object()):
        validate_uri(uri)


@pytest.mark.parametrize("uri", ["ftp://host/path", "/tmp/deker", "deker", ""])
def test_other_schemes_are_rejected(uri):
    with pytest.raises(ClickException, match="Invalid uri"):
        validate_uri(uri)


@pytest.mark.parametrize(
    ("uri", "distribution"),
    [
        ("https://deker.example.com", "deker-server-adapters"),
        ("http://localhost:8000", "deker-server-adapters"),
        ("file:///tmp/deker", "deker-local-adapters"),
    ],
)
def test_missing_adapters_are_reported_with_the_install_command(uri, distribution):
    with patch.object(utils, "find_spec", return_value=None):
        with pytest.raises(ClickException, match=f"not installed, run: pip install {distribution}"):
            validate_uri(uri)
