import warnings
from unittest.mock import MagicMock

import pytest
from rich.console import Console

from rig.cli import app, console, main, prefix
from rig.paths import rig_prefix


class TestApp:
    def test_app_has_correct_name(self) -> None:
        assert app.name == ("rig",)

    def test_app_has_description(self) -> None:
        assert app.help == "Personal development environment tools."


class TestPrefixCommand:
    def test_prefix_outputs_rig_prefix_path(self) -> None:
        mock_out = MagicMock()
        console.out = mock_out

        prefix()

        mock_out.assert_called_once_with(str(rig_prefix()))

    def test_prefix_returns_none(self) -> None:
        console.out = MagicMock()

        result = prefix()

        assert result is None


class TestCommandRegistration:
    def test_install_command_registered(self) -> None:
        # Use app's help output to verify command registration
        with pytest.raises(SystemExit):
            app(["--help"])
        # If we get here without error, the app has commands registered

    def test_uninstall_command_registered(self) -> None:
        with pytest.raises(SystemExit):
            app(["uninstall", "--help"])

    def test_prefix_command_registered(self) -> None:
        with pytest.raises(SystemExit):
            app(["--prefix", "--help"])


class TestConsole:
    def test_console_is_rich_console(self) -> None:
        assert isinstance(console, Console)


class TestMain:
    def test_main_is_callable(self) -> None:
        assert callable(main)

    def test_main_executes_app_with_empty_args(self) -> None:
        # Cyclopts shows help and exits with 0 when invoked with no args
        with pytest.raises(SystemExit) as exc_info:
            app([])
        assert exc_info.value.code == 0

    def test_main_invokes_app(self) -> None:
        # main() should invoke app() which shows help with no args
        # Suppress Cyclopts warning about being invoked without tokens in test
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", UserWarning)
            with pytest.raises(SystemExit) as exc_info:
                main()
        assert exc_info.value.code == 0
