from unittest.mock import MagicMock, patch

import pytest

from click.testing import CliRunner

from deker_shell import main, namespace, utils
from deker_shell.consts import DEFAULT_HISTORY_FILE, DEFAULT_HISTORY_SIZE, help_start
from deker_shell.main import parse_extra_value, start

runner = CliRunner()


class TestStart:
    def test_start_correct(self):
        """Tests if deker_shell starts correctly with correct uri."""
        result = runner.invoke(start, ["file:///tmp/deker"])
        assert result.exit_code == 0
        # the REPL prompt is only rendered by the first REPL in a process, so don't depend on test order
        assert result.output.startswith(f"{help_start}\n")
        assert result.output.endswith("Exiting Deker\n")

    @pytest.mark.parametrize("uri", ["http://localhost:8000", "https://user:password@deker.example.com"])
    def test_start_with_server_uri(self, uri):
        """A server uri reaches the Deker client untouched; the client itself is mocked, there is no server."""
        with patch.object(main, "Client") as client, patch.object(utils, "find_spec", return_value=object()):
            client.return_value.is_closed = False
            client.return_value.__iter__.return_value = iter([])
            with patch.object(main, "embed", side_effect=EOFError), patch("asyncio.get_running_loop"):
                result = runner.invoke(start, [uri])
        assert result.exit_code == 0
        client.assert_called_once_with(uri)

    def test_start_without_server_adapters_explains_what_to_install(self):
        with patch.object(utils, "find_spec", return_value=None):
            result = runner.invoke(start, ["https://deker.example.com"])
        assert result.exit_code == 1
        assert result.output == (
            "Error: Deker adapters for 'https://' are not installed, run: pip install deker-server-adapters\n"
        )

    def test_start_fail_bad_uri(self):
        """Tests if deker_shell fails to start if uri is wrong."""
        result = runner.invoke(start, ["invalid-uri"])
        assert result.exit_code == 1
        assert result.output == "Error: Invalid uri\n"

    def test_start_fail_no_args(self):
        """Tests if deker_shell fails to start if no args given."""
        result = runner.invoke(start, [])
        assert result.exit_code == 2
        assert (
            result.output == "Usage: start [OPTIONS] URI\n"
            "Try 'start --help' for help.\n"
            "\n"
            "Error: Missing argument 'URI'.\n"
        )

    @pytest.mark.parametrize(
        "params",
        [
            [
                "file:///tmp/deker",
                "--workers",
                "4",
                "--write-lock-timeout",
                "30",
                "--write-lock-check-interval",
                "20",
                "--loglevel",
                "INFO",
                "--memory-limit",
                "512M",
            ],
            ["file:///tmp/deker", "-w", "4", "-t", "30", "-c", "20", "-l", "INFO", "-m", "512M"],
        ],
    )
    def test_start_with_parameters(self, params):
        """Tests if deker_shell fails to start if no args given."""
        result = runner.invoke(start, params)
        assert result.exit_code == 0

    def test_start_with_extra_parameters(self):
        """Tests if deker_shell fails to start if no args given."""
        result = runner.invoke(start, ["file:///tmp/deker", "--key.inner_key", "test", "-k", "t"])
        assert result.exit_code == 0

    def test_start_with_py_file_fail(self):
        result = runner.invoke(start, ["no_file.py"])
        assert result.exit_code == 1
        assert result.output == "Error: File does not exist\n"

    def test_dotted_extra_parameters_are_grouped(self):
        """``--conf.a 1 --conf.b 2`` builds one nested dict, the second key does not wipe the first."""
        # a plain MagicMock, not the AsyncMock patch would pick for a coroutine function: asyncio.run is patched too
        with patch.object(main, "interactive_shell", new_callable=MagicMock) as shell:
            with patch.object(main.asyncio, "run"):
                result = runner.invoke(start, ["file:///tmp/deker", "--conf.a", "1", "--conf.b", "2", "--flag", "x"])
        assert result.exit_code == 0
        shell.assert_called_once_with(
            "file:///tmp/deker", DEFAULT_HISTORY_FILE, DEFAULT_HISTORY_SIZE, conf={"a": 1, "b": 2}, flag="x"
        )

    def test_history_options_reach_the_shell(self, tmp_path):
        with patch.object(main, "interactive_shell", new_callable=MagicMock) as shell:
            with patch.object(main.asyncio, "run"):
                result = runner.invoke(
                    start, ["file:///tmp/deker", "--history-file", str(tmp_path / "h"), "--history-size", "7"]
                )
        assert result.exit_code == 0
        shell.assert_called_once_with("file:///tmp/deker", tmp_path / "h", 7)

    def test_history_size_must_be_positive(self):
        result = runner.invoke(start, ["file:///tmp/deker", "--history-size", "0"])
        assert result.exit_code == 2
        assert "--history-size" in result.output

    @pytest.mark.parametrize(
        ("raw", "expected"),
        [
            ("10", 10),
            ("1.5", 1.5),
            ("True", True),
            ("None", None),
            ("[1, 2]", [1, 2]),
            ("text", "text"),
            ("/tmp/x", "/tmp/x"),
        ],
    )
    def test_extra_values_become_literals_when_they_are_literals(self, raw, expected):
        assert parse_extra_value(raw) == expected

    def test_shell_history_is_written_to_the_given_file(self, tmp_path):
        """A real REPL run ends at EOF; the history file is created on the way."""
        history_file = tmp_path / "history"
        result = runner.invoke(start, ["file:///tmp/deker", "--history-file", str(history_file)])
        assert result.exit_code == 0
        assert history_file.parent.exists()

    def test_closed_client_stops_the_shell(self):
        closed_client = MagicMock(spec=main.Client, is_closed=True)
        closed_client.__iter__.return_value = iter([])
        with patch.object(main, "Client", return_value=closed_client):
            result = runner.invoke(start, ["file:///tmp/deker"])
        assert result.exit_code == 1
        assert "Client is closed" in result.output
        closed_client.close.assert_called_once()

    def test_eof_stops_the_loop(self):
        with patch.object(main, "embed", side_effect=EOFError), patch("asyncio.get_running_loop") as loop:
            result = runner.invoke(start, ["file:///tmp/deker"])
        assert result.exit_code == 0
        loop.return_value.stop.assert_called_once()
        assert result.output.endswith("Exiting Deker\n")

    def test_failed_client_leaves_nothing_to_close(self):
        with patch.object(namespace, "client", None), patch.object(main, "Client", side_effect=ValueError("boom")):
            result = runner.invoke(start, ["file:///tmp/deker"])
        assert result.exit_code == 1
        assert "Exiting Deker" not in result.output


if __name__ == "__main__":
    pytest.main()
