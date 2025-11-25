---
description: Performance review
argument-hint: [files or directories]
---

Use the @agent-performance-architect agent to perform a **performance review** on: $ARGUMENTS

If no files/directories specified, review `src/`.

## Focus areas

- **Hot paths**: Identify performance-critical code
- **Algorithms**: O(n) vs O(n^2) complexity
- **Memory**: Allocation patterns, generators vs lists
- **Caching**: Appropriate use of lru_cache
- **I/O**: Efficient file/network handling
- **Benchmarks**: Critical paths have benchmarks

## Review methodology

1. **Profile first**: Use py-spy or cProfile data
2. **Identify bottlenecks**: Find actual hot paths
3. **Analyze algorithms**: Check complexity
4. **Recommend improvements**: Targeted optimizations

## Output

Save to `reviews/performance-review-YYYY-MM-DD-HHmmss.md`:

```markdown
# Performance review - [Date/Time]

## Scope
[Files reviewed]

## Profiling data
[If available, key metrics]

## Hot paths identified
[Critical code paths]

## Optimization opportunities
[Improvements with expected impact]

## Recommendations
[Prioritized performance improvements]

## Compliance
- [ ] Critical paths identified
- [ ] Benchmarks exist for hot paths
- [ ] No obvious O(n^2) where O(n) possible
- [ ] Appropriate caching
```
