---
description: Documentation review
argument-hint: [files or directories]
---

Use the @agent-documentation-reviewer agent to perform a **documentation review** on: $ARGUMENTS

If no files/directories specified, review `docs/` and docstrings in `src/`.

## Focus areas

- **Headlines**: Sentence case only (NEVER title case)
- **Docstrings**: Google-style for public APIs
- **Diagrams**: Mermaid.js only (NEVER ASCII art)
- **Examples**: Complete and tested
- **Diataxis**: Correct quadrant placement
- **Vale**: Prose quality linting

## Review criteria

**CRITICAL violations:**

- Title case headlines
- ASCII art diagrams
- Missing docstrings on public APIs
- Test docstrings (should NOT have any)

**Important improvements:**

- Incorrect Diataxis quadrant
- Incomplete code examples
- Vale errors
- Missing cross-references

## Output

Save to `reviews/docs-review-YYYY-MM-DD-HHmmss.md`:

```markdown
# Documentation review - [Date/Time]

## Scope
[Files reviewed]

## Formatting issues
[Headlines, diagrams, structure]

## Content issues
[Accuracy, completeness, examples]

## Diataxis assessment
[Correct quadrant placement]

## Recommendations
[Documentation improvements]

## Compliance
- [ ] Sentence case headlines
- [ ] Mermaid.js diagrams
- [ ] Google-style docstrings
- [ ] No test docstrings
- [ ] Vale passes
```
