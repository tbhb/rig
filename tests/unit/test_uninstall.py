import os
from typing import TYPE_CHECKING
from unittest.mock import patch

import pytest

from rig.commands._install import SHIM_SENTINEL
from rig.commands._uninstall import uninstall

if TYPE_CHECKING:
    from pathlib import Path


class TestUninstallCommand:
    def test_removes_rig_managed_shim(self, tmp_path: Path) -> None:
        shim_path = tmp_path / "rig"
        shim_path.write_text(f"#!/bin/bash\n{SHIM_SENTINEL}\necho hello")

        with patch.dict(os.environ, {"RIG_SHIM_PATH": str(shim_path)}):
            uninstall()

        assert not shim_path.exists()

    def test_refuses_to_remove_non_rig_file(self, tmp_path: Path) -> None:
        shim_path = tmp_path / "rig"
        shim_path.write_text("#!/bin/bash\necho other")

        with (
            patch.dict(os.environ, {"RIG_SHIM_PATH": str(shim_path)}),
            pytest.raises(SystemExit),
        ):
            uninstall()

        # File should still exist
        assert shim_path.exists()

    def test_handles_missing_shim_gracefully(self, tmp_path: Path) -> None:
        shim_path = tmp_path / "nonexistent"

        with patch.dict(os.environ, {"RIG_SHIM_PATH": str(shim_path)}):
            # Should not raise
            uninstall()
