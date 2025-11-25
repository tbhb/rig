---
description: Standards compliance review
argument-hint: [files or directories]
---

Use the @agent-code-reviewer agent to perform a **standards compliance review** on: $ARGUMENTS

If no files/directories specified, review `src/` and `tests/`.

## Focus areas

- **Python execution**: `uv run python` (NEVER bare python)
- **Design principles**: SOLID, DRY, YAGNI, KISS
- **Code organization**: Private modules, public API via `__init__.py`
- **Naming**: PascalCase classes, snake_case functions
- **Immutability**: @dataclass(slots=True, frozen=True)
- **Dependencies**: Standard library first

## Standards references

- `.claude/standards/design-principles.md`
- `.claude/standards/quality-gates.md`
- `.claude/standards/python-execution.md`
- `.claude/standards/test-standards.md`
- `.claude/standards/documentation-standards.md`

## Output

Save to `reviews/standards-review-YYYY-MM-DD-HHmmss.md`:

```markdown
# Standards compliance review - [Date/Time]

## Scope
[Files reviewed]

## Violations by category

### Python execution
[uv run usage issues]

### Design principles
[SOLID, DRY, YAGNI, KISS violations]

### Code organization
[Module structure issues]

### Naming conventions
[Naming issues]

## Recommendations
[Prioritized fixes]

## Compliance
- [ ] uv run for all Python execution
- [ ] SOLID principles followed
- [ ] DRY - no code duplication
- [ ] YAGNI - no speculative features
- [ ] KISS - simple solutions preferred
- [ ] Naming conventions followed
```
