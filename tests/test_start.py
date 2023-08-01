from unittest.mock import patch

import pytest

from deker_shell.consts import help_start
from deker_shell.main import start


class TestStart:
    def test_start_correct(self, capsys):
        """Tests if deker_shell starts correctly with correct uri."""
        with patch("sys.argv", ["deker", "file:///tmp/test/"]):
            start()
            assert capsys.readouterr().out == f"{help_start}\n> >\r\n"

    def test_start_fail_bad_uri(self, capsys):
        """Tests if deker_shell fails to start if uri is wrong."""
        with patch("sys.argv", ["deker", "test"]):
            with pytest.raises(ValueError):
                start()

    def test_start_fail_no_args(self, capsys):
        """Tests if deker_shell fails to start if no args given."""
        with patch("sys.argv", ["deker"]):
            start()
            assert capsys.readouterr().out == "No params passed\n"


if __name__ == "__main__":
    pytest.main()
