import sys
from importlib.metadata import PackageNotFoundError
from unittest.mock import patch

from rig import __version__


class TestVersion:
    def test_version_is_string(self) -> None:
        assert isinstance(__version__, str)

    def test_version_not_empty(self) -> None:
        assert len(__version__) > 0

    def test_version_is_unknown_when_package_not_found(self) -> None:
        # Remove rig from sys.modules to force reimport
        modules_to_remove = [key for key in sys.modules if key.startswith("rig")]
        for mod in modules_to_remove:
            del sys.modules[mod]

        # Patch version to raise PackageNotFoundError
        with patch(
            "importlib.metadata.version",
            side_effect=PackageNotFoundError("rig"),
        ):
            import rig  # noqa: PLC0415

            assert rig.__version__ == "unknown"

        # Restore original modules
        for mod in modules_to_remove:
            if mod in sys.modules:
                del sys.modules[mod]
        import rig as rig_restored  # noqa: PLC0415

        assert rig_restored.__version__ == __version__
