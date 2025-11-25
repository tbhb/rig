# Design principles

**MANDATORY: Apply fundamental principles to ALL code**

These fundamental design principles guide ALL implementation decisions. They must be applied rigorously to maintain code quality.

## Core principles

### SOLID principles

**ALWAYS apply in architecture:**

- **Single Responsibility**: Each component MUST have one clear purpose
- **Open/Closed**: Design code to be modifiable without breaking existing behavior. NEVER create extension points until you add the second use case.
- **Liskov Substitution**: Abstractions MUST be substitutable without breaking behavior
- **Interface Segregation**: MUST define focused protocols for different concerns
- **Dependency Inversion**: ALWAYS depend on abstractions (protocols) NOT concrete implementations

### DRY (Don't Repeat Yourself)

**NEVER duplicate logic:**

- MUST extract common patterns into reusable functions
- MUST use type-based dispatch or pattern matching to eliminate conditional duplication
- MUST share validation logic across similar types
- MUST create reusable error message generators to maintain consistency

### YAGNI (You Aren't Gonna Need It)

**ONLY implement current requirements:**

- NEVER add speculative features "for future use"
- MUST resist premature abstractions - solve concrete problems first, generalize when you see the pattern
- NEVER build generic "plugin systems" or "extension frameworks" until explicitly needed

### KISS (Keep It Simple, Stupid)

**ALWAYS prefer simplicity:**

- Use straightforward algorithms over clever optimizations until profiling proves necessity
- Prefer clear `if/else` chains over complex pattern matching when readability is better
- **KISS takes precedence** - a simple solution that works beats an "elegant" complex one
- NEVER use clever type system tricks; prefer obvious, maintainable type definitions

### Secure by default

**Default configuration should be the secure configuration:**

- Require explicit opt-in for less secure behavior rather than users having to actively secure the system
- Validate input at system boundaries
- Use multiple layers of validation and security controls (Defense in Depth)

### Defense in depth

**Use multiple layers of validation and security controls:**

- Failure of one layer doesn't compromise the system
- Validate at multiple levels: parsing, type conversion, business logic
- Never rely on a single validation layer

### Measure, don't guess

**Always profile and benchmark before optimizing:**

- Performance work without measurements is speculation
- NEVER optimize without profiling data showing a bottleneck
- Use `pytest-benchmark` for systematic performance tracking
- Apply "Avoid Premature Optimization" principle

### Pay for what you use

**Abstractions should impose no runtime overhead for unused features:**

- Users shouldn't pay performance costs for capabilities they don't need
- Use `@dataclass(slots=True)` to reduce memory overhead
- Lazy initialization for expensive resources

### Avoid premature optimization

**Get it correct first, measure where bottlenecks actually are, then optimize the hot paths:**

- Complements YAGNI - don't optimize code that isn't even slow yet
- Profile first, optimize second
- Focus on algorithmic efficiency (O(n) vs O(n^2)) before micro-optimizations

### Balance

**Apply principles pragmatically:**

- Apply SOLID/DRY rigorously for maintainability
- Apply Secure by Default for safety
- Apply Measure Don't Guess for performance
- But KISS takes precedence when complexity doesn't demand sophistication

## Application examples

**Good - Follows SOLID, DRY, KISS:**

```python
@dataclass(slots=True, frozen=True)
class ProcessResult:
    """Simple, immutable result with clear responsibility."""
    data: dict[str, Any]
    items: list[str]

def validate_count(values: list[str], min_count: int, max_count: int | None) -> None:
    """Reusable validation - DRY applied."""
    if len(values) < min_count:
        raise ValidationError(f"Expected at least {min_count} values")
    if max_count is not None and len(values) > max_count:
        raise ValidationError(f"Expected at most {max_count} values")
```

**Bad - Violates YAGNI, KISS:**

```python
class ExtensibleFramework:
    """Over-engineered before we have a second use case."""
    def __init__(self):
        self.plugins = []
        self.middleware = []
        self.hooks = defaultdict(list)

    def register_plugin(self, plugin: Plugin) -> None:
        # Speculative extension point - violates YAGNI
        ...
```

## References

These principles are applied throughout:

- Code implementation (all modules)
- Architecture decisions
- Performance optimization
- Security design
- Testing strategy

For project-specific applications, see:

- `.claude/standards/quality-gates.md` - How principles enforce quality
- `.claude/standards/test-standards.md` - How principles apply to testing
- `CLAUDE.md` - Project-wide development standards
