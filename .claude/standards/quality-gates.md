# Quality gates

**CRITICAL: Before completing ANY changes, ALL of these MUST pass**

## Mandatory quality checks

### 1. Type checking

**MUST pass with ZERO errors:**

```bash
uv run basedpyright
```

- ZERO TOLERANCE for type errors
- Comprehensive type hints REQUIRED for ALL code in `src/` and `tests/`
- Use `typing-extensions` for modern typing features
- NO `# type: ignore` without EXPLICIT user confirmation

### 2. Linting

**ALL checks MUST pass:**

```bash
uv run ruff check .
```

- ZERO TOLERANCE for lint violations
- NO `# noqa` or `# ruff: noqa` without EXPLICIT user confirmation
- Fix root cause, NEVER suppress warnings

### 3. Formatting

**Code MUST be formatted:**

```bash
uv run ruff format .
```

- Consistent formatting across codebase
- Run before committing

### 4. Tests

**ALL tests MUST pass with >95% coverage:**

```bash
uv run pytest
uv run pytest --cov src --cov-report term-missing --cov-report html --cov-branch
```

- MANDATORY >95% test coverage for all new code
- NEVER submit code reducing coverage below threshold
- Both example-based AND property-based tests required
- All tests MUST pass - no exceptions

### 5. Documentation

**Public APIs MUST have Google-style docstrings:**

- Public APIs: MANDATORY comprehensive docstrings
- Private members: ONLY document when NOT self-explanatory
- **CRITICAL: Test functions/classes MUST NOT have docstrings**
- Test names MUST be self-explanatory: `test_<scenario>_<expected_result>`

### 6. Pre-commit hooks

**NEVER bypass hooks:**

```bash
# Let pre-commit hooks run automatically
git commit -m "feat: add new functionality"

# NEVER use --no-verify, --no-gpg-sign, or flags that skip hooks
```

- If a hook fails, fix the issues and commit again
- If hook modifies files, stage changes and commit again
- Understand WHY hook failed, don't bypass it

## Quality standards

### ZERO TOLERANCE policy

There is NO SUCH THING as an "acceptable" type error or lint warning:

- ALL violations MUST be fixed
- NEVER suppressed as "acceptable"
- NO exceptions

### User confirmation for ignores

NEVER add ignore comments without EXPLICIT user confirmation:

- `# type: ignore`, `# pyright: ignore`
- `# noqa`, `# ruff: noqa`
- ALWAYS ask user first
- Explain why ignore might be needed

### Python execution

**CRITICAL: ALL Python execution MUST use `uv run python`**

See `.claude/standards/python-execution.md` for details.

### Test organization

**Domain-centric organization REQUIRED:**

- CORRECT: `test_processing.py`, `test_validation.py`
- NEVER: `test_coverage_gaps.py`, `test_edge_cases.py`, `test_final_push.py`

See `.claude/standards/test-standards.md` for details.

## Workflow integration

### Before starting work

1. Pull latest changes: `git pull origin main`
2. Create feature branch: `git checkout -b feat/feature-name`
3. Verify environment: `uv sync`

### During development

1. Write code in small, logical units
2. Run type checker after each unit: `uv run basedpyright`
3. Run tests after each unit: `uv run pytest`
4. NEVER skip validation steps

### Before committing

1. Run linter: `uv run ruff check .`
2. Run formatter: `uv run ruff format .`
3. Run all tests: `uv run pytest`
4. Check coverage: `uv run pytest --cov src --cov-report term-missing`
5. Stage changes: `git add <files>`
6. Commit with conventional format: `git commit -m "feat: add feature"`
7. Let pre-commit hooks run (NEVER bypass)

### Before PR

1. Ensure ALL quality gates pass
2. Review changes yourself first
3. Push to remote: `git push -u origin feat/feature-name`
4. Create PR: `gh pr create --title "feat: add feature" --body "Description"`

## CI/CD requirements

All PRs should pass CI checks across:

- Multiple operating systems (Ubuntu, macOS, Windows)
- Multiple Python versions (3.14+)

Failure on ANY platform or version blocks merge.

## References

For related standards, see:

- `.claude/standards/design-principles.md` - Design principles enforcing quality
- `.claude/standards/python-execution.md` - Python execution requirements
- `.claude/standards/test-standards.md` - Testing standards and organization
- `CLAUDE.md` - Complete development workflow
