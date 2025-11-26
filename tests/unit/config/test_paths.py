from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from rig.config import (
    get_global_config_path,
    get_local_config_path,
    get_project_config_path,
)

# Import worktree path utility - will be implemented in Stage 4
try:
    from rig.config._paths import get_worktree_config_path
except ImportError:
    get_worktree_config_path = None


class TestGetGlobalConfigPath:
    def test_returns_local_rig_config_toml(self) -> None:
        with patch.object(Path, "home", return_value=Path("/home/user")):
            result = get_global_config_path()

        assert result == Path("/home/user/.local/rig/config.toml")

    def test_returns_absolute_path(self) -> None:
        result = get_global_config_path()
        assert result.is_absolute()

    def test_path_ends_with_config_toml(self) -> None:
        result = get_global_config_path()
        assert result.name == "config.toml"
        assert result.parent.name == "rig"


class TestGetProjectConfigPath:
    def test_returns_rig_toml_in_project_root(self) -> None:
        project_root = Path("/home/user/projects/myapp")
        result = get_project_config_path(project_root)
        assert result == project_root / ".rig.toml"

    def test_returns_absolute_path_for_absolute_input(self) -> None:
        project_root = Path("/home/user/projects/myapp")
        result = get_project_config_path(project_root)
        assert result.is_absolute()

    def test_path_has_correct_suffix(self) -> None:
        project_root = Path("/project")
        result = get_project_config_path(project_root)
        assert result.name == ".rig.toml"


class TestGetLocalConfigPath:
    def test_returns_rig_local_toml_in_project_root(self) -> None:
        project_root = Path("/home/user/projects/myapp")
        result = get_local_config_path(project_root)
        assert result == project_root / ".rig.local.toml"

    def test_returns_absolute_path_for_absolute_input(self) -> None:
        project_root = Path("/home/user/projects/myapp")
        result = get_local_config_path(project_root)
        assert result.is_absolute()

    def test_path_has_correct_suffix(self) -> None:
        project_root = Path("/project")
        result = get_local_config_path(project_root)
        assert result.name == ".rig.local.toml"


@pytest.mark.skipif(
    get_worktree_config_path is None,
    reason="get_worktree_config_path not yet implemented",
)
class TestGetWorktreeConfigPath:
    def test_returns_rig_worktree_toml_in_worktree(self) -> None:
        assert get_worktree_config_path is not None
        worktree_path = Path("/home/user/projects/myapp-feature")
        result = get_worktree_config_path(worktree_path)
        assert result == worktree_path / ".rig.worktree.toml"

    def test_returns_absolute_path_for_absolute_input(self) -> None:
        assert get_worktree_config_path is not None
        worktree_path = Path("/home/user/worktrees/feature-branch")
        result = get_worktree_config_path(worktree_path)
        assert result.is_absolute()

    def test_path_has_correct_suffix(self) -> None:
        assert get_worktree_config_path is not None
        worktree_path = Path("/worktree")
        result = get_worktree_config_path(worktree_path)
        assert result.name == ".rig.worktree.toml"

    def test_works_with_complex_paths(self) -> None:
        assert get_worktree_config_path is not None
        worktree_path = Path("/Users/user/Code/github.com/org/repo-feature-branch")
        result = get_worktree_config_path(worktree_path)
        assert result == worktree_path / ".rig.worktree.toml"

    def test_path_parent_is_worktree_path(self) -> None:
        assert get_worktree_config_path is not None
        worktree_path = Path("/some/worktree/path")
        result = get_worktree_config_path(worktree_path)
        assert result.parent == worktree_path
