# Python execution requirements

**CRITICAL: Environment isolation is MANDATORY**

## Core requirement

**ALL Python execution MUST use `uv run python`:**

- NEVER use bare `python` or `python3`
- This ensures proper environment isolation
- Prevents dependency conflicts
- Uses project-specific Python version and dependencies

## Common commands

### Script execution

```bash
# CORRECT
uv run python scripts/analyze.py
uv run python scripts/benchmark_compare.py
uv run python -c "import yourpackage; print(yourpackage.__version__)"

# WRONG
python scripts/analyze.py
python3 scripts/analyze.py
```

### Module execution

```bash
# CORRECT
uv run python -m pdb test_file.py
uv run python -m cProfile -o profile.prof script.py
uv run python -m timeit "import yourpackage"

# WRONG
python -m pdb test_file.py
python3 -m cProfile script.py
```

### Testing

```bash
# CORRECT
uv run pytest
uv run pytest tests/unit/
uv run pytest tests/unit/test_module.py::test_function_name
uv run pytest --cov src --cov-report html

# WRONG
pytest
pytest tests/unit/
```

### Type checking

```bash
# CORRECT
uv run basedpyright
uv run basedpyright src/

# WRONG
basedpyright
pyright
```

### Linting and formatting

```bash
# CORRECT
uv run ruff check .
uv run ruff format .
uv run ruff check src/ --fix

# WRONG
ruff check .
ruff format .
```

### Interactive Python

```bash
# CORRECT
uv run python
# Then import packages and experiment

# WRONG
python
python3
```

## Profiling and performance

### CPU profiling

```bash
# CORRECT - cProfile
uv run python -m cProfile -o profile.prof -s cumulative script.py

# CORRECT - Analyze with pstats
uv run python -c "
import pstats
p = pstats.Stats('profile.prof')
p.sort_stats('cumulative')
p.print_stats(20)
"

# WRONG
python -m cProfile script.py
```

### Benchmarking

```bash
# CORRECT
uv run pytest --benchmark-only
uv run pytest tests/benchmarks/

# WRONG
pytest --benchmark-only
```

### Timing

```bash
# CORRECT
uv run python -m timeit -s "import yourpackage" "yourpackage.process()"

# WRONG
python -m timeit "..."
```

## Documentation tools

```bash
# CORRECT
uv run mkdocs serve
uv run mkdocs build

# Note: Use `just dev-docs` or `just build-docs` when available
```

## Why this matters

### 1. Environment isolation

Using `uv run python` ensures:

- Correct Python version (project-specified)
- Project dependencies are available
- No conflicts with system Python or other projects

### 2. Consistency

Everyone on the team uses:

- Same Python version
- Same dependency versions
- Same execution environment

### 3. Reproducibility

Commands work identically:

- On different developer machines
- In CI/CD pipelines
- Across different operating systems

## Common mistakes

### WRONG - Bare Python

```bash
# DON'T DO THIS
python scripts/analyze.py
python3 -m pytest
python -m cProfile script.py
```

### WRONG - Direct tool invocation

```bash
# DON'T DO THIS
pytest
basedpyright
ruff check .
```

### CORRECT - Always use uv run

```bash
# DO THIS INSTEAD
uv run python scripts/analyze.py
uv run pytest
uv run basedpyright
uv run ruff check .
```

## Exceptions

There are NO exceptions to this rule. Always use `uv run python` or `uv run <tool>`.

## References

For related requirements, see:

- `.claude/standards/quality-gates.md` - Quality checks requiring `uv run`
- `.claude/standards/test-standards.md` - Test execution with `uv run`
- `CLAUDE.md` - Development workflow
