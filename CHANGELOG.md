# Changelog

All notable changes to this project will be documented in this file.

This project does not use semantic versioning. Changes are organized chronologically.

## Unreleased

### Added

- Configuration system with layered TOML files
  - Global config (`~/.local/rig/config.toml`)
  - Ancestor configs (discovered walking up directory tree)
  - Project config (`.rig.toml`)
  - Local config (`.rig.local.toml`)
- Multi-layer config resolution with precedence
- Extend/exclude modifiers for list fields in configuration
- TOML file discovery and parsing with validation
- Core configuration data structures and schema
- `rig install` - Install shim to `~/.local/bin/rig`
- `rig uninstall` - Remove the shim
- `rig --prefix` - Print repository path
- Basic CLI framework using cyclopts
