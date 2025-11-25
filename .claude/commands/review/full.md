---
description: Comprehensive code review covering all project standards
argument-hint: [files or directories]
---

Use the @agent-code-reviewer, @agent-documentation-reviewer and @agent-performance-architect agents to perform a **comprehensive code review** on: $ARGUMENTS

If no files/directories specified, review `src/` and `tests/`.

## Review scope

This is a full review covering all quality dimensions:

- **Security**: Vulnerabilities, injection risks, secure defaults
- **Type safety**: Annotations, basedpyright compliance, typing-extensions usage
- **Performance**: Efficiency, hot paths, potential bottlenecks
- **Test coverage**: Organization, coverage metrics, property-based testing
- **Specification adherence**: Contract compliance
- **Documentation**: Docstrings, headline formatting, self-documenting code
- **Standards compliance**: Python tooling (`uv run`), naming conventions, code organization

## Methodology

1. **Initial assessment**: Identify scope, read relevant standards
2. **Systematic analysis**: Review each dimension methodically
3. **Feedback synthesis**: Categorize findings by severity

## Standards references

- `.claude/standards/design-principles.md` - Design principles (SOLID, DRY, YAGNI, KISS)
- `.claude/standards/quality-gates.md` - Quality requirements
- `.claude/standards/python-execution.md` - Python execution (`uv run`)
- `.claude/standards/documentation-standards.md` - Documentation requirements
- `.claude/standards/test-standards.md` - Test organization
- `.claude/agents/code-reviewer.md` - Full review methodology

## Critical constraints

- **NEVER** modify code in `src/` or `tests/`
- **MUST** reference specific file paths and line numbers
- **MUST** distinguish: CRITICAL (must fix), IMPORTANT (should fix), OPTIONAL (nice to have)
- **FLAG** any `# type: ignore`, `# pyright: ignore`, `# noqa` as CRITICAL unless documented

## Output

Save review to `reviews/full-review-YYYY-MM-DD-HHmmss.md` using this format:

```markdown
# Full code review - [Date/Time]

## Summary
[High-level assessment of overall code quality]

## Scope
- Files reviewed: [list]
- Primary focus: Comprehensive review

## Critical issues (MUST FIX)
[Security vulnerabilities, bugs, severe maintainability problems]

## Important suggestions (SHOULD FIX)
[Significant quality improvements]

## Optional improvements (NICE TO HAVE)
[Minor enhancements]

## Positive observations
[Well-executed patterns worth noting]

## Compliance check
- [ ] Follows project design principles
- [ ] Python tooling uses `uv run` prefix
- [ ] Uses `typing-extensions` appropriately
- [ ] Proper error handling
- [ ] Adequate documentation
- [ ] Security best practices
- [ ] Performance considerations
- [ ] Test coverage >95%
- [ ] ZERO type/lint violations

## Recommendations
[Prioritized action items]
```
