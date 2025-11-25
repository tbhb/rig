---
description: Test coverage and quality review
argument-hint: [files or directories]
---

Use the @agent-code-reviewer and @agent-test-architect agents to perform a **test review** on: $ARGUMENTS

If no files/directories specified, review `tests/`.

## Focus areas

- **Coverage**: >95% required, branch coverage enabled
- **Organization**: Domain-centric (NOT task-centric)
- **Naming**: `test_<scenario>_<expected_result>`
- **Property-based**: Hypothesis tests for invariants
- **Fuzz testing**: Atheris for robustness
- **Benchmarks**: Critical path performance

## Review criteria

**CRITICAL violations:**

- Coverage below 95%
- Task-centric test files (test_edge_cases.py, test_coverage_gaps.py)
- Test docstrings (names should be self-explanatory)

**Important improvements:**

- Missing property-based tests
- Missing fuzz tests for input handling
- Missing benchmarks for critical paths
- Poor test isolation

## Output

Save to `reviews/tests-review-YYYY-MM-DD-HHmmss.md`:

```markdown
# Test review - [Date/Time]

## Scope
[Test files reviewed]

## Coverage summary
[Current coverage percentage]

## Organization issues
[Domain vs task-centric problems]

## Missing tests
[Coverage gaps, missing property tests]

## Recommendations
[Test improvements needed]

## Compliance
- [ ] Coverage >95%
- [ ] Domain-centric organization
- [ ] No test docstrings
- [ ] Property-based tests present
- [ ] Naming follows convention
```
