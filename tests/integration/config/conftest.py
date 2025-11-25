from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from pathlib import Path


@pytest.fixture
def temp_home(tmp_path: Path) -> Path:
    home = tmp_path / "home"
    home.mkdir()
    return home


@pytest.fixture
def global_config_dir(temp_home: Path) -> Path:
    config_dir = temp_home / ".local" / "rig"
    config_dir.mkdir(parents=True)
    return config_dir


@pytest.fixture
def global_config_file(global_config_dir: Path) -> Path:
    config_file = global_config_dir / "config.toml"
    config_file.write_text(
        """\
[worktree]
default-location = "sibling"
delete-branch = true
protected = false

[worktree.paths]
sibling = "../{repo}-{branch}"
local = ".worktrees/{branch}"
pr = "../{repo}-pr-{number}"
"""
    )
    return config_file


@pytest.fixture
def project_dir(tmp_path: Path) -> Path:
    project = tmp_path / "projects" / "my-project"
    project.mkdir(parents=True)
    git_dir = project / ".git"
    git_dir.mkdir()
    return project


@pytest.fixture
def project_config_file(project_dir: Path) -> Path:
    config_file = project_dir / ".rig.toml"
    config_file.write_text(
        """\
[worktree]
default-location = "local"

[worktree.sync]
link = [".env", "node_modules"]
copy = ["config.local.json"]

[worktree.hooks]
post-add = ["npm install", "make setup"]
"""
    )
    return config_file


@pytest.fixture
def local_config_file(project_dir: Path) -> Path:
    config_file = project_dir / ".rig.local.toml"
    config_file.write_text(
        """\
[worktree]
protected = true

[worktree.sync]
extend-link = [".venv"]
exclude-copy = ["config.local.json"]
"""
    )
    return config_file


@pytest.fixture
def ancestor_config_dir(project_dir: Path) -> Path:
    return project_dir.parent


@pytest.fixture
def ancestor_config_file(ancestor_config_dir: Path) -> Path:
    config_file = ancestor_config_dir / ".rig.toml"
    config_file.write_text(
        """\
[worktree]
delete-branch = false

[worktree.paths]
sibling = "../wt/{branch}"

[worktree.hooks]
post-add = ["echo 'Ancestor hook'"]
"""
    )
    return config_file


@pytest.fixture
def multi_ancestor_hierarchy(tmp_path: Path) -> dict[str, Path]:
    root = tmp_path / "workspace"
    root.mkdir()

    org = root / "org"
    org.mkdir()

    team = org / "team"
    team.mkdir()

    project = team / "project"
    project.mkdir()
    (project / ".git").mkdir()

    root_config = root / ".rig.toml"
    root_config.write_text(
        """\
[worktree]
default-location = "sibling"

[worktree.sync]
link = [".env"]
"""
    )

    org_config = org / ".rig.toml"
    org_config.write_text(
        """\
[worktree]
delete-branch = false

[worktree.sync]
extend-link = [".secrets"]
"""
    )

    team_config = team / ".rig.toml"
    team_config.write_text(
        """\
[worktree.paths]
sibling = "../{repo}-wt-{branch}"

[worktree.hooks]
post-add = ["team-setup.sh"]
"""
    )

    project_config = project / ".rig.toml"
    project_config.write_text(
        """\
[worktree]
protected = true

[worktree.sync]
extend-link = ["node_modules"]
exclude-link = [".secrets"]

[worktree.hooks]
extend-post-add = ["npm install"]
"""
    )

    return {
        "root": root,
        "org": org,
        "team": team,
        "project": project,
        "root_config": root_config,
        "org_config": org_config,
        "team_config": team_config,
        "project_config": project_config,
    }


@pytest.fixture
def empty_project_dir(tmp_path: Path) -> Path:
    project = tmp_path / "empty-project"
    project.mkdir()
    (project / ".git").mkdir()
    return project


@pytest.fixture
def invalid_toml_config(project_dir: Path) -> Path:
    config_file = project_dir / ".rig.toml"
    config_file.write_text(
        """\
[worktree
invalid syntax here
"""
    )
    return config_file


@pytest.fixture
def invalid_schema_config(project_dir: Path) -> Path:
    config_file = project_dir / ".rig.toml"
    config_file.write_text(
        """\
[worktree]
default-location = "invalid_value"
unknown_field = true

[unknown_section]
key = "value"
"""
    )
    return config_file


@pytest.fixture
def config_with_all_extend_exclude(project_dir: Path) -> Path:
    config_file = project_dir / ".rig.toml"
    config_file.write_text(
        """\
[worktree.sync]
link = ["base-link"]
copy = ["base-copy"]
extend-link = ["extra-link"]
extend-copy = ["extra-copy"]
exclude-link = ["removed-link"]
exclude-copy = ["removed-copy"]

[worktree.hooks]
post-add = ["base-post-add"]
pre-remove = ["base-pre-remove"]
extend-post-add = ["extra-post-add"]
extend-pre-remove = ["extra-pre-remove"]
exclude-post-add = ["removed-post-add"]
exclude-pre-remove = ["removed-pre-remove"]
"""
    )
    return config_file


SAMPLE_GLOBAL_CONFIG = """\
[worktree]
default-location = "sibling"
delete-branch = true
protected = false

[worktree.paths]
sibling = "../{repo}-{branch}"
local = ".worktrees/{branch}"
pr = "../{repo}-pr-{number}"

[worktree.sync]
link = []
copy = []

[worktree.hooks]
post-add = []
pre-remove = []
"""

SAMPLE_PROJECT_CONFIG = """\
[worktree]
default-location = "local"

[worktree.sync]
link = [".env", "node_modules"]

[worktree.hooks]
post-add = ["npm install"]
"""

SAMPLE_LOCAL_CONFIG = """\
[worktree]
protected = true

[worktree.sync]
extend-link = [".venv"]
"""
