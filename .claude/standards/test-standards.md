# Test standards

**MANDATORY: Comprehensive testing requirements**

## Core requirements

### Test coverage

**MANDATORY: >95% coverage for all code**

```bash
# Check coverage
uv run pytest --cov src --cov-report term-missing --cov-report html --cov-branch
```

- NEVER submit code reducing coverage below 95%
- Both example-based AND property-based tests REQUIRED
- Branch coverage MUST be enabled

### Test types

**Multiple test types required:**

1. **Unit tests** - Test individual components in isolation
2. **Integration tests** - Test component interactions
3. **Property-based tests** (Hypothesis) - Discover edge cases automatically
4. **Benchmark tests** (pytest-benchmark) - Track performance

## Test organization

### Directory structure

```text
tests/
├── unit/              # Unit tests organized by domain
│   ├── core/
│   ├── validators/
│   ├── converters/
│   └── services/
├── integration/       # Integration tests
├── properties/        # Property-based tests
└── benchmarks/        # Performance benchmarks
```

### Domain-centric organization

**CRITICAL: Tests MUST be organized by domain/feature, NOT by testing purpose**

CORRECT - Domain-centric organization:

- `test_validation.py` - All validation tests
- `test_processing.py` - All data processing tests
- `test_conversion.py` - All type conversion tests
- `test_storage.py` - All storage/persistence tests

NEVER - Purpose-centric organization:

- `test_coverage_gaps.py` - Organized by testing task
- `test_edge_cases.py` - Organized by test category
- `test_final_push.py` - Organized by development phase
- `test_final_coverage.py` - Organized by testing goal

**Rationale:**

- Tests for a feature should be consolidated into domain-specific files
- Regardless of when they were written or what testing goal prompted their creation
- Makes finding and maintaining tests easier
- Prevents test file proliferation

## Test naming standards

### MANDATORY pattern

**Test functions MUST follow: `test_<scenario>_<expected_result>`**

The test name alone should clearly communicate:

- What is being tested
- The expected outcome
- Without reading any docstring

### Context-aware naming

**MUST leverage class names - NEVER repeat information already in context:**

```python
# CORRECT - Context-aware
class TestDataProcessing:
    def test_single_item_processes_successfully(self):
        # Clear: testing data processing, single item, success
        ...

    def test_batch_processing_handles_empty_input(self):
        # Clear: testing data processing, batch mode, empty input
        ...

# WRONG - Redundant with class name
class TestDataProcessing:
    def test_data_processing_single_item_processes_successfully(self):
        # "data_processing" is redundant with class name
        ...
```

### Consistent patterns

**Use these patterns based on test type:**

**Success cases:**

```python
def test_valid_input_processes_successfully(self):
    # Test successful behavior
    ...

def test_multiple_items_collected_in_list(self):
    # Test successful multi-value handling
    ...
```

**Error cases:**

```python
def test_insufficient_items_raises_validation_error(self):
    # Specific error type mentioned
    ...

def test_invalid_type_raises_type_error(self):
    # Clear about what error is expected
    ...
```

**Validation cases:**

```python
def test_count_validation_passes_with_correct_count(self):
    # Clear: validation passes with specific condition
    ...

def test_count_validation_fails_with_too_many_items(self):
    # Clear: validation fails with specific condition
    ...
```

**Edge cases:**

```python
def test_empty_string_value_allowed(self):
    # Specific edge case identified
    ...

def test_unicode_names_supported(self):
    # Specific edge case tested
    ...
```

### Prefer concise names

**ALWAYS prefer concise names over verbose "and" chains:**

```python
# CORRECT - Concise
def test_multiple_short_options_clustered(self):
    ...

# WRONG - Verbose
def test_parser_accepts_multiple_short_options_and_clusters_them_together(self):
    ...
```

## Test docstrings

### CRITICAL: NO test docstrings

**Test functions and test classes MUST NOT have docstrings:**

```python
# CORRECT - No docstring, self-explanatory name
def test_single_item_processes_correctly(self):
    processor = Processor(config)
    result = processor.process(["item"])
    assert result.data["item"] == "processed"

# WRONG - Has docstring
def test_single_item_processes_correctly(self):
    """Test that single items process correctly."""  # NEVER add docstrings!
    processor = Processor(config)
    result = processor.process(["item"])
    assert result.data["item"] == "processed"
```

**Rationale:**

- Test names should be self-explanatory
- If name needs a docstring to explain it, the name is wrong
- Improve the name instead of adding a docstring

## Property-based testing

### When to use Hypothesis

**MUST add property-based tests for:**

- Features that handle varying input
- Validation logic with multiple constraints
- Type conversion with diverse inputs
- Any algorithm that should work for broad input space

### Example pattern

```python
from hypothesis import given, strategies as st

@given(
    item_count=st.integers(min_value=1, max_value=50),
    value_count=st.integers(min_value=0, max_value=100),
)
def test_handles_variable_counts(
    item_count: int,
    value_count: int,
) -> None:
    # Hypothesis generates diverse combinations
    spec = build_spec(num_items=item_count)
    args = build_args(num_values=value_count)

    result = processor.process(args)

    # Property: Result should always have valid structure
    assert isinstance(result, ProcessResult)
    assert len(result.items) <= item_count
```

### Test data strategies

Use Hypothesis strategies to generate:

- Valid and invalid inputs
- Various patterns and formats
- Edge case values (empty strings, very long strings, Unicode)
- Boundary conditions (min/max values)

## Benchmark tests

### Organization

```text
tests/benchmarks/
├── microbenchmarks/  # Fine-grained operation benchmarks
├── integration/      # End-to-end realistic scenarios
└── memory/          # Memory profiling benchmarks
```

### Naming convention

```python
# Microbenchmarks
def test_benchmark_process_single(benchmark):
    ...

def test_benchmark_process_batch(benchmark):
    ...

# Memory benchmarks
def test_memory_large_input_peak_usage(benchmark):
    ...
```

### Requirements

- MUST verify correctness (assert result is correct)
- MUST use `benchmark` fixture from pytest-benchmark
- NO docstrings (same rule as unit tests)

## Test execution

### Running tests

```bash
# All tests
uv run pytest

# Specific test file
uv run pytest tests/unit/test_module.py

# Specific test function
uv run pytest tests/unit/test_module.py::test_function_name

# With coverage
uv run pytest --cov src --cov-report term-missing --cov-branch

# Property-based tests with stats
uv run pytest tests/properties/ --hypothesis-show-statistics

# Benchmarks only
uv run pytest tests/benchmarks/ --benchmark-only
```

### Debugging failed tests

```bash
# Verbose output
uv run pytest -v

# Stop on first failure
uv run pytest -x

# Show local variables on failure
uv run pytest -l

# Debug with pdb
uv run pytest --pdb

# Hypothesis-specific debugging
uv run pytest --hypothesis-verbosity=verbose
uv run pytest --hypothesis-seed=12345  # Reproduce specific failure
```

## Quality checklist

Before considering tests complete:

- [ ] >95% coverage achieved
- [ ] ALL tests pass
- [ ] Domain-centric organization (not purpose-centric)
- [ ] Test names follow `test_<scenario>_<expected_result>` pattern
- [ ] NO test docstrings (names are self-explanatory)
- [ ] Property-based tests for appropriate features
- [ ] Benchmark tests for performance-critical paths
- [ ] Tests organized by feature domain
- [ ] Edge cases covered
- [ ] Error cases tested

## References

For related standards:

- `.claude/standards/quality-gates.md` - Coverage requirements
- `.claude/standards/python-execution.md` - Running tests with `uv run`
- `CLAUDE.md` - Complete testing strategy
