import os
import stat
from pathlib import Path
from unittest.mock import patch

import pytest

from rig.commands._install import (
    SHIM_SENTINEL,
    _print_path_instructions,
    generate_shim_content,
    get_shim_path,
    install,
    is_in_path,
    is_rig_managed_shim,
)


class TestGetShimPath:
    def test_returns_path_in_local_bin(self) -> None:
        result = get_shim_path()
        assert result == Path.home() / ".local" / "bin" / "rig"


class TestIsInPath:
    def test_directory_in_path(self, tmp_path: Path) -> None:
        with patch.dict(os.environ, {"PATH": str(tmp_path)}):
            assert is_in_path(tmp_path) is True

    def test_directory_not_in_path(self, tmp_path: Path) -> None:
        with patch.dict(os.environ, {"PATH": "/usr/bin:/bin"}):
            assert is_in_path(tmp_path) is False

    def test_resolved_path_in_path(self, tmp_path: Path) -> None:
        # Create a symlink scenario
        resolved = tmp_path.resolve()
        with patch.dict(os.environ, {"PATH": str(resolved)}):
            assert is_in_path(tmp_path) is True


class TestIsRigManagedShim:
    def test_returns_false_for_nonexistent_file(self, tmp_path: Path) -> None:
        nonexistent = tmp_path / "nonexistent"
        assert is_rig_managed_shim(nonexistent) is False

    def test_returns_true_for_rig_managed_shim(self, tmp_path: Path) -> None:
        shim = tmp_path / "rig"
        _ = shim.write_text(f"#!/bin/bash\n{SHIM_SENTINEL}\necho hello")
        assert is_rig_managed_shim(shim) is True

    def test_returns_false_for_non_rig_file(self, tmp_path: Path) -> None:
        other_file = tmp_path / "rig"
        _ = other_file.write_text("#!/bin/bash\necho hello")
        assert is_rig_managed_shim(other_file) is False


class TestGenerateShimContent:
    def test_includes_sentinel(self) -> None:
        content = generate_shim_content(Path("/some/path"))
        assert SHIM_SENTINEL in content

    def test_includes_project_path(self) -> None:
        project_path = Path("/my/project")
        content = generate_shim_content(project_path)
        assert str(project_path) in content

    def test_includes_shebang(self) -> None:
        content = generate_shim_content(Path("/some/path"))
        assert content.startswith("#!/usr/bin/env bash")

    def test_includes_strict_mode(self) -> None:
        content = generate_shim_content(Path("/some/path"))
        assert "set -euo pipefail" in content

    def test_includes_exec_command(self) -> None:
        project_path = Path("/my/project")
        content = generate_shim_content(project_path)
        assert f"exec uv run --project '{project_path}' rig" in content

    def test_escapes_single_quotes_in_path(self) -> None:
        project_path = Path("/my/project's/path")
        content = generate_shim_content(project_path)
        # Single quotes should be escaped as '\''
        assert "'/my/project'\\''s/path'" in content

    def test_handles_spaces_in_path(self) -> None:
        project_path = Path("/my project/path with spaces")
        content = generate_shim_content(project_path)
        # Path should be quoted
        assert "'/my project/path with spaces'" in content


class TestPrintPathInstructions:
    def test_prints_warning_with_bin_dir(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        bin_dir = Path("/home/user/.local/bin")
        _print_path_instructions(bin_dir)
        captured = capsys.readouterr()
        assert "/home/user/.local/bin" in captured.out
        assert "not in your PATH" in captured.out

    def test_prints_bash_instructions(self, capsys: pytest.CaptureFixture[str]) -> None:
        bin_dir = Path("/home/user/.local/bin")
        _print_path_instructions(bin_dir)
        captured = capsys.readouterr()
        assert "For bash" in captured.out
        assert "~/.bashrc" in captured.out

    def test_prints_zsh_instructions(self, capsys: pytest.CaptureFixture[str]) -> None:
        bin_dir = Path("/home/user/.local/bin")
        _print_path_instructions(bin_dir)
        captured = capsys.readouterr()
        assert "For zsh" in captured.out
        assert "~/.zshrc" in captured.out

    def test_prints_path_export(self, capsys: pytest.CaptureFixture[str]) -> None:
        bin_dir = Path("/home/user/.local/bin")
        _print_path_instructions(bin_dir)
        captured = capsys.readouterr()
        assert 'export PATH="$HOME/.local/bin:$PATH"' in captured.out


class TestInstallCommand:
    @pytest.fixture
    def mock_bin_dir(self, tmp_path: Path) -> Path:
        bin_dir = tmp_path / ".local" / "bin"
        bin_dir.mkdir(parents=True)
        return bin_dir

    def test_creates_bin_dir_if_missing(self, tmp_path: Path) -> None:
        shim_path = tmp_path / ".local" / "bin" / "rig"
        bin_dir = shim_path.parent
        project_dir = tmp_path / "project"
        project_dir.mkdir()

        with patch.dict(
            os.environ,
            {
                "RIG_SHIM_PATH": str(shim_path),
                "RIG_PREFIX": str(project_dir),
                "PATH": str(bin_dir),
            },
        ):
            install()

        assert bin_dir.exists()
        assert shim_path.exists()

    def test_writes_executable_shim(self, mock_bin_dir: Path, tmp_path: Path) -> None:
        shim_path = mock_bin_dir / "rig"
        project_dir = tmp_path / "project"
        project_dir.mkdir()

        with patch.dict(
            os.environ,
            {
                "RIG_SHIM_PATH": str(shim_path),
                "RIG_PREFIX": str(project_dir),
                "PATH": str(mock_bin_dir),
            },
        ):
            install()

        assert shim_path.exists()
        mode = shim_path.stat().st_mode
        assert mode & stat.S_IXUSR

    def test_exits_if_bin_dir_not_in_path(
        self, mock_bin_dir: Path, tmp_path: Path
    ) -> None:
        shim_path = mock_bin_dir / "rig"
        project_dir = tmp_path / "project"
        project_dir.mkdir()

        with (
            patch.dict(
                os.environ,
                {
                    "RIG_SHIM_PATH": str(shim_path),
                    "RIG_PREFIX": str(project_dir),
                    "PATH": "/usr/bin:/bin",
                },
            ),
            pytest.raises(SystemExit),
        ):
            install()

    def test_prompts_for_non_rig_existing_file(
        self, mock_bin_dir: Path, tmp_path: Path
    ) -> None:
        shim_path = mock_bin_dir / "rig"
        shim_path.write_text("#!/bin/bash\necho other")
        project_dir = tmp_path / "project"
        project_dir.mkdir()

        with (
            patch.dict(
                os.environ,
                {
                    "RIG_SHIM_PATH": str(shim_path),
                    "RIG_PREFIX": str(project_dir),
                    "PATH": str(mock_bin_dir),
                },
            ),
            patch("rig.commands._install.Confirm.ask", return_value=False),
            pytest.raises(SystemExit),
        ):
            install()

    def test_overwrites_existing_rig_shim_silently(
        self, mock_bin_dir: Path, tmp_path: Path
    ) -> None:
        shim_path = mock_bin_dir / "rig"
        shim_path.write_text(f"#!/bin/bash\n{SHIM_SENTINEL}\nold content")

        new_project = tmp_path / "new_project"
        new_project.mkdir()

        with patch.dict(
            os.environ,
            {
                "RIG_SHIM_PATH": str(shim_path),
                "RIG_PREFIX": str(new_project),
                "PATH": str(mock_bin_dir),
            },
        ):
            install()

        content = shim_path.read_text()
        assert str(new_project) in content
