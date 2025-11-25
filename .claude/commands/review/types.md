---
description: Type safety review
argument-hint: [files or directories]
---

Use the @agent-code-reviewer agent to perform a **type safety review** on: $ARGUMENTS

If no files/directories specified, review `src/`.

## Focus areas

- **Type annotations**: Comprehensive hints on all functions/methods
- **basedpyright compliance**: Zero errors required
- **typing-extensions usage**: ReadOnly, TypeIs, Doc where appropriate
- **Type narrowing**: Proper use of isinstance, TypeIs
- **Generic types**: Correct use of TypeVar, Generic, Protocol
- **TypedDict**: Immutable configurations with ReadOnly

## Review criteria

**CRITICAL violations:**

- Missing type annotations
- `# type: ignore` without justification
- `# pyright: ignore` without justification
- Use of `Any` where specific types possible

**Important improvements:**

- TypedDict instead of plain dict for structured data
- ReadOnly for immutable TypedDict fields
- TypeIs instead of TypeGuard for narrowing
- Protocol for structural typing

## Output

Save to `reviews/types-review-YYYY-MM-DD-HHmmss.md`:

```markdown
# Type safety review - [Date/Time]

## Scope
[Files reviewed]

## basedpyright status
[Current error count, if any]

## Critical issues
[Type errors, missing annotations]

## Improvements
[Better type patterns to apply]

## Compliance
- [ ] All functions annotated
- [ ] basedpyright passes with zero errors
- [ ] No unjustified type: ignore
- [ ] typing-extensions used appropriately
```
