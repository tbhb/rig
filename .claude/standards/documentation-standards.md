# Documentation standards

**MANDATORY: Documentation quality requirements**

## Headline formatting

### Sentence case requirement

**CRITICAL: ALL documentation headlines (H1-H6) MUST use sentence case**

- Capitalize ONLY the first word and proper nouns
- NEVER use title case for headlines

**Examples:**

CORRECT:

- "Configuration design principles"
- "What is validation?"
- "REST-style API"
- "API reference"

WRONG:

- "Configuration Design Principles" (title case)
- "What Is Validation?" (title case)

**Proper nouns and acronyms remain capitalized:**

- Python, GitHub, API, CLI, HTTP, JSON, YAML, POSIX

### Applies to

- All markdown files
- README files
- Documentation in comments/docstrings
- Code review reports
- Any written documentation

## Code documentation

### Public APIs

**MANDATORY: Google-style docstrings for ALL public APIs**

```python
def process_data(items: list[str]) -> ProcessResult:
    """Process data items into structured result.

    This function processes a list of data items and returns a
    structured ProcessResult containing the processed data and metadata.

    Args:
        items: List of data items to process.

    Returns:
        ProcessResult containing processed data and any additional
        metadata about the operation.

    Raises:
        ProcessingError: If items violate expected format.
        ValidationError: If validation constraints are violated.

    Example:
        >>> result = process_data(["item1", "item2"])
        >>> result.processed
        True
        >>> result.items
        ['item1', 'item2']
    """
```

### Private members

**ONLY document when NOT self-explanatory:**

```python
# CORRECT - Self-explanatory, no docstring needed
def _validate_count(values: list[str], min_count: int, max_count: int | None) -> None:
    if len(values) < min_count:
        raise ValidationError(f"Expected at least {min_count} values")

# CORRECT - Complex logic, docstring helpful
def _resolve_conflicts(
    options: dict[str, list[str]],
    conflicts: dict[str, set[str]],
) -> dict[str, list[str]]:
    """Resolve conflicting options by precedence rules.

    When multiple conflicting options are provided, applies precedence
    rules to determine which option takes effect. Later options override
    earlier ones unless explicit conflict resolution is configured.
    """
```

### Test documentation

**CRITICAL: Test functions and classes MUST NOT have docstrings**

See `.claude/standards/test-standards.md` for test naming requirements.

## Prose quality

### Vale linting

**MANDATORY: ALL documentation MUST pass Vale linting**

```bash
# Sync Vale styles (first time or after updates)
vale sync

# Lint all documentation
vale docs/

# Lint specific file
vale docs/explanation/architecture.md

# Run all documentation linters
just lint-markdown
```

### Common Vale issues

- **Passive voice** -> Rewrite in active voice
- **Complex sentences** -> Break into shorter sentences
- **Jargon** -> Define technical terms on first use
- **Inconsistent terminology** -> Use consistent terms
- **Spelling errors** -> Fix typos
- **Wordiness** -> Use concise language

**NEVER skip or ignore Vale errors** - achieve zero errors before completion.

## Structure

### Document organization

- **Clear hierarchy** with appropriate headings (h1 for title, h2 for sections)
- **Table of contents** for documents >500 words
- **Cross-references** to related documentation
- **Code blocks** with syntax highlighting (`python`, `bash`)

### Code blocks

Always specify language for syntax highlighting:

````markdown
```python
def example():
    return "highlighted"
```

```bash
uv run pytest
```
````

## Diagrams

### Mermaid.js requirement

**MANDATORY: ALWAYS use Mermaid.js for ALL diagrams**

See `.claude/standards/diagram-requirements.md` for complete requirements.

**Never create ASCII art diagrams.**

## Examples

### All examples MUST be tested

**CRITICAL: ALL code examples MUST:**

- Be accurate and verified to work
- Include complete context for reproduction
- Use proper syntax highlighting
- Show realistic use cases
- Include expected output/results for commands
- Reference specific file paths when relevant

```python
# CORRECT - Complete, tested example
from yourpackage import Config

# Define configuration
config = Config(
    name="example",
    settings={"verbose": True, "debug": False},
)

# Use configuration
result = config.process()
print(result.status)  # Output: success
```

## Language and tone

### Technical and precise

- Write for experienced Python developers
- Be concise and direct - fact-based, no unnecessary verbosity
- Use emphatic keywords for requirements: ALWAYS, MANDATORY, MUST, CRITICAL, NEVER

### Active voice

**ALWAYS use active voice:**

CORRECT: "The processor validates data"
WRONG: "Data is validated by the processor"

CORRECT: "The function converts types automatically"
WRONG: "Types are converted automatically by the function"

### Flowing prose

Use flowing prose for explanations:

- Bullets only for discrete items, steps, or lists
- Write connected paragraphs for concepts and rationale
- Let ideas flow naturally through the text

## Diataxis framework

### Documentation organization

Documentation should follow the Diataxis framework:

| User Need | Quadrant | Directory | Purpose |
|-----------|----------|-----------|---------|
| "I want to learn" | Tutorials | `docs/tutorials/` | Hands-on lessons teaching fundamentals |
| "I want to accomplish X" | How-to Guides | `docs/guides/` | Step-by-step problem-solving procedures |
| "I want to understand" | Explanation | `docs/explanation/` | Conceptual discussions, architecture, rationale |
| "I need to look up X" | Reference | `docs/reference/` | Technical specifications, API docs, lookup info |

**Choose the right quadrant based on user need.**

See documentation-architect and documentation-reviewer agents for complete Diataxis guidance.

## Quality checklist

Before considering documentation complete:

- [ ] Headlines use sentence case (not title case)
- [ ] Public APIs have Google-style docstrings
- [ ] Private members documented ONLY when not self-explanatory
- [ ] NO test docstrings
- [ ] Passes `vale docs/` or `just lint-docs` with zero errors
- [ ] All code examples tested and verified to work
- [ ] Diagrams use Mermaid.js (no ASCII art)
- [ ] Active voice used appropriately
- [ ] Cross-references included where relevant
- [ ] Organized in appropriate Diataxis quadrant
- [ ] Terminology consistent with existing docs

## References

For related standards:

- `.claude/standards/diagram-requirements.md` - Diagram creation
- `.claude/standards/test-standards.md` - Test documentation prohibition
- `CLAUDE.md` - Complete documentation workflow
- `documentation-architect.md` - Agent for creating documentation
- `documentation-reviewer.md` - Agent for reviewing documentation
