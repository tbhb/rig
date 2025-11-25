import os
import tempfile
from pathlib import Path
from unittest.mock import patch

from hypothesis import given, strategies as st

from rig.commands._install import (
    SHIM_SENTINEL,
    generate_shim_content,
    is_in_path,
    is_rig_managed_shim,
)

# Strategy for valid path characters (excluding null bytes and path separators)
path_segment = st.text(
    alphabet=st.characters(
        categories=["L", "N", "P", "S"],
        exclude_characters="\x00/\\",
    ),
    min_size=1,
    max_size=50,
)

# Strategy for valid PATH directory entries (no null bytes or surrogates)
path_dir_text = st.text(
    alphabet=st.characters(
        exclude_characters="\x00",
        exclude_categories=["Cs"],  # Exclude Unicode surrogates
    ),
    min_size=1,
    max_size=100,
)


class TestIsInPathProperties:
    @given(path_dirs=st.lists(path_dir_text, min_size=1, max_size=10))
    def test_directory_found_when_present(self, path_dirs: list[str]) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            # Add tmp_path to the list
            all_dirs = [*path_dirs, str(tmp_path)]
            path_str = os.pathsep.join(all_dirs)

            with patch.dict(os.environ, {"PATH": path_str}):
                assert is_in_path(tmp_path) is True

    @given(path_dirs=st.lists(path_dir_text, min_size=0, max_size=10))
    def test_directory_not_found_when_absent(self, path_dirs: list[str]) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            # Ensure tmp_path is not in the list
            filtered = [d for d in path_dirs if d != str(tmp_path)]
            path_str = os.pathsep.join(filtered)

            with patch.dict(os.environ, {"PATH": path_str}):
                assert is_in_path(tmp_path) is False


class TestGenerateShimContentProperties:
    @given(segments=st.lists(path_segment, min_size=1, max_size=5))
    def test_always_contains_sentinel(self, segments: list[str]) -> None:
        project_path = Path("/") / "/".join(segments)
        content = generate_shim_content(project_path)
        assert SHIM_SENTINEL in content

    @given(segments=st.lists(path_segment, min_size=1, max_size=5))
    def test_always_starts_with_shebang(self, segments: list[str]) -> None:
        project_path = Path("/") / "/".join(segments)
        content = generate_shim_content(project_path)
        assert content.startswith("#!/usr/bin/env bash")

    @given(segments=st.lists(path_segment, min_size=1, max_size=5))
    def test_always_has_strict_mode(self, segments: list[str]) -> None:
        project_path = Path("/") / "/".join(segments)
        content = generate_shim_content(project_path)
        assert "set -euo pipefail" in content

    @given(segments=st.lists(path_segment, min_size=1, max_size=5))
    def test_path_is_single_quoted(self, segments: list[str]) -> None:
        project_path = Path("/") / "/".join(segments)
        content = generate_shim_content(project_path)
        # The path should be wrapped in single quotes
        assert "--project '" in content

    def test_single_quotes_are_escaped(self) -> None:
        # Property: single quotes in paths must be escaped
        project_path = Path("/it's/o'reilly's/book")
        content = generate_shim_content(project_path)
        # Single quotes should be escaped as '\''
        assert "it'\\''s" in content
        assert "o'\\''reilly'\\''s" in content


class TestShellMetacharacterSafety:
    def test_backticks_are_safely_quoted(self) -> None:
        # Backticks should not execute commands when path is single-quoted
        project_path = Path("/path/with/`whoami`/injection")
        content = generate_shim_content(project_path)
        # Path is single-quoted, so backticks are literal
        assert "'/path/with/`whoami`/injection'" in content

    def test_dollar_signs_are_safely_quoted(self) -> None:
        # Dollar signs should not expand variables when path is single-quoted
        project_path = Path("/path/with/$HOME/var")
        content = generate_shim_content(project_path)
        # Path is single-quoted, so $HOME is literal
        assert "'/path/with/$HOME/var'" in content

    def test_double_quotes_are_safely_quoted(self) -> None:
        # Double quotes inside single quotes are literal
        project_path = Path('/path/with/"double"/quotes')
        content = generate_shim_content(project_path)
        assert "'/path/with/\"double\"/quotes'" in content

    def test_newlines_in_path_are_preserved(self) -> None:
        # Newlines in paths should be preserved (though unusual)
        project_path = Path("/path/with\nnewline")
        content = generate_shim_content(project_path)
        # The path should be quoted and contain the newline
        assert "'/path/with\nnewline'" in content

    def test_semicolons_are_safely_quoted(self) -> None:
        # Semicolons should not terminate commands when path is single-quoted
        project_path = Path("/path;rm -rf /;test")
        content = generate_shim_content(project_path)
        assert "'/path;rm -rf /;test'" in content

    def test_ampersands_are_safely_quoted(self) -> None:
        # Ampersands should not background commands when path is single-quoted
        project_path = Path("/path&background&test")
        content = generate_shim_content(project_path)
        assert "'/path&background&test'" in content

    def test_pipes_are_safely_quoted(self) -> None:
        # Pipes should not redirect output when path is single-quoted
        project_path = Path("/path|cat /etc/passwd|test")
        content = generate_shim_content(project_path)
        assert "'/path|cat /etc/passwd|test'" in content

    @given(
        special_chars=st.sampled_from(
            ["`", "$", '"', ";", "&", "|", "(", ")", "<", ">", "\\", "!"]
        )
    )
    def test_shell_metacharacters_are_safely_quoted(self, special_chars: str) -> None:
        # All shell metacharacters should be safely quoted
        project_path = Path(f"/path/with/{special_chars}/char")
        content = generate_shim_content(project_path)
        # The exec line should contain the path in single quotes
        assert f"--project '/path/with/{special_chars}/char'" in content


class TestIsRigManagedShimProperties:
    @given(segments=st.lists(path_segment, min_size=1, max_size=5))
    def test_generated_shim_is_recognized(self, segments: list[str]) -> None:
        # Property: shims generated by generate_shim_content are recognized
        project_path = Path("/") / "/".join(segments)
        content = generate_shim_content(project_path)

        with tempfile.TemporaryDirectory() as tmp:
            shim_file = Path(tmp) / "test_shim"
            _ = shim_file.write_text(content)
            assert is_rig_managed_shim(shim_file) is True

    @given(content=st.text(min_size=0, max_size=1000))
    def test_arbitrary_content_without_sentinel_not_recognized(
        self, content: str
    ) -> None:
        # Property: arbitrary content without sentinel is not recognized
        # (unless it accidentally contains the sentinel)
        if SHIM_SENTINEL in content:
            return  # Skip this case

        with tempfile.TemporaryDirectory() as tmp:
            shim_file = Path(tmp) / "test_file"
            _ = shim_file.write_text(content)
            assert is_rig_managed_shim(shim_file) is False
