from pathlib import Path

from rig.paths import rig_prefix


class TestRigPrefix:
    def test_returns_path_object(self) -> None:
        result = rig_prefix()

        assert isinstance(result, Path)

    def test_returns_project_root(self) -> None:
        result = rig_prefix()

        # The prefix should contain pyproject.toml (project root)
        assert (result / "pyproject.toml").exists()

    def test_returns_resolved_path(self) -> None:
        result = rig_prefix()

        # Path should be absolute and resolved
        assert result.is_absolute()
        assert ".." not in str(result)

    def test_contains_src_directory(self) -> None:
        result = rig_prefix()

        # Project root should have src directory
        assert (result / "src").exists()
        assert (result / "src").is_dir()
