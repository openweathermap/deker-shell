import os
import pytest

from click.testing import CliRunner

from deker_shell.consts import help_start
from deker_shell.main import start

runner = CliRunner()


class TestStart:
    def test_start_correct(self):
        """Tests if deker_shell starts correctly with correct uri."""
        result = runner.invoke(start, ["file:///tmp/deker"])
        assert result.exit_code == 0
        assert result.output == f"{help_start}\n>  >\nExiting Deker\n"

    def test_start_fail_bad_uri(self):
        """Tests if deker_shell fails to start if uri is wrong."""
        result = runner.invoke(start, ['invalid-uri'])
        assert result.exit_code == 1
        assert result.output == "Error: Invalid uri\n"

    def test_start_fail_no_args(self):
        """Tests if deker_shell fails to start if no args given."""
        result = runner.invoke(start, [])
        assert result.exit_code == 2
        assert result.output == "Usage: start [OPTIONS] URI\n" \
                                "Try 'start --help' for help.\n" \
                                "\n" \
                                "Error: Missing argument 'URI'.\n"

    @pytest.mark.parametrize(
        "params", [
            [
                "file:///tmp/deker",
                "--workers", "4",
                "--write-lock-timeout", "30",
                "--write-lock-check-interval", "20",
                "--loglevel", "INFO",
                "--memory-limit", "512M"
            ],
            [
                "file:///tmp/deker",
                "-w", "4",
                "-t", "30",
                "-c", "20",
                "-l", "INFO",
                "-m", "512M"
            ]
        ]
    )
    def test_start_with_parameters(self, params):
        """Tests if deker_shell fails to start if no args given."""
        result = runner.invoke(start, params)
        assert result.exit_code == 0

    def test_start_with_extra_parameters(self):
        """Tests if deker_shell fails to start if no args given."""
        result = runner.invoke(start, ["file:///tmp/deker", "--key.inner_key", "test", "-k", "t"])
        assert result.exit_code == 0

    def test_start_with_py_file(self):
        result = runner.invoke(start, ["__init__.py"])
        assert result.exit_code == 0

    def test_start_with_py_file_fail(self):
        result = runner.invoke(start, ["no_file.py"])
        assert result.exit_code == 1
        assert result.output == "Error: File does not exist\n"


if __name__ == "__main__":
    pytest.main()
