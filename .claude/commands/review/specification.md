---
description: Comprehensive specification review for design documents
argument-hint: [spec files]
---

Use the @agent-code-reviewer, @agent-specification-architect, @agent-api-designer, @agent-documentation-reviewer, and @agent-performance-architect agents **in parallel** to perform a **comprehensive specification review** on: $ARGUMENTS

If no files specified, review all files in `specs/`.

## Review scope

This is a multi-dimensional specification review covering:

- **Completeness**: All requirements defined, edge cases covered, acceptance criteria clear
- **Clarity**: Unambiguous language, RFC 2119 keywords, clear terminology
- **API design**: Ergonomic interfaces, type safety, consistency with existing patterns
- **Documentation standards**: Sentence case headlines, Mermaid.js diagrams, proper structure
- **Performance implications**: Algorithmic complexity, scalability considerations, hot paths identified
- **Implementation feasibility**: Realistic scope, clear dependencies, testable requirements
- **Test requirements**: Coverage expectations, property-based test opportunities, integration test needs

## Review methodology

**Run all agents in parallel** by invoking them in a single message:

1. **specification-architect**: Overall spec quality, completeness, RFC 2119 compliance
2. **api-designer**: API design, type safety, ergonomics, consistency
3. **documentation-reviewer**: Headlines, diagrams, structure, Diataxis quadrant
4. **performance-architect**: Performance implications, complexity analysis, scalability
5. **code-reviewer**: Implementation feasibility, standards compliance, security considerations

## Standards references

- `.claude/standards/documentation-standards.md` - Documentation requirements
- `.claude/standards/design-principles.md` - Design principles (SOLID, DRY, YAGNI, KISS)
- `.claude/agents/specification-architect.md` - Specification methodology
- `.claude/agents/api-designer.md` - API design principles
- `CLAUDE.md` - Project-specific standards

## Critical violations

**MUST be fixed before implementation:**

- Title case headlines (use sentence case)
- ASCII art diagrams (use Mermaid.js)
- Missing acceptance criteria
- Ambiguous requirements (no RFC 2119 keywords)
- Undefined edge cases
- Missing performance considerations for hot paths
- Untestable requirements
- Security risks not addressed

## Output format

Each agent saves their findings to `reviews/specification-review-YYYY-MM-DD-HHmmss.md` in their designated section:

```markdown
# Specification review - [Spec name] - [Date/Time]

## Summary
[High-level assessment across all dimensions]

## Specification analyzed
- **File**: [path]
- **Purpose**: [brief description]
- **Reviewers**: specification-architect, api-designer, documentation-reviewer, performance-architect, code-reviewer

---

## Specification architect review

### Completeness assessment
[Are all requirements defined? Edge cases covered?]

### Clarity assessment
[Ambiguous language? Proper RFC 2119 usage?]

### Structure assessment
[Logical organization? Clear dependencies?]

### Acceptance criteria
[Are acceptance criteria testable and complete?]

---

## API designer review

### Interface design
[Ergonomic? Type-safe? Consistent with existing patterns?]

### Error handling
[Error cases defined? User-facing messages clear?]

### Backward compatibility
[Breaking changes identified? Migration path defined?]

### Consistency
[Follows project conventions? Naming aligned?]

---

## Documentation reviewer review

### Formatting compliance
- [ ] Sentence case headlines (NEVER title case)
- [ ] Mermaid.js diagrams (NEVER ASCII art)
- [ ] Proper structure (TOC, sections)

### Content quality
[Clarity? Examples? Cross-references?]

### Diataxis assessment
[Correct quadrant? Technical reference vs guide?]

---

## Performance architect review

### Hot path identification
[Which operations are performance-critical?]

### Complexity analysis
[Algorithm complexity? O(n) implications?]

### Scalability considerations
[How does this scale? Resource usage?]

### Benchmark requirements
[Which paths need benchmarks?]

---

## Code reviewer review

### Implementation feasibility
[Can this be implemented as specified?]

### Security considerations
[Input validation? Injection risks? Secure defaults?]

### Test requirements
[Unit tests? Property tests? Integration tests?]

### Dependencies
[External dependencies? Compatibility concerns?]

---

## Critical issues (MUST FIX)
[Issues that block implementation]

## Important suggestions (SHOULD FIX)
[Significant quality improvements before implementation]

## Optional improvements (NICE TO HAVE)
[Minor enhancements]

## Positive observations
[Well-designed aspects worth noting]

## Compliance checklist
- [ ] All requirements complete and unambiguous
- [ ] RFC 2119 keywords used appropriately
- [ ] Sentence case headlines throughout
- [ ] Mermaid.js diagrams only
- [ ] API design is ergonomic and type-safe
- [ ] Performance implications documented
- [ ] Security considerations addressed
- [ ] Test requirements defined
- [ ] Acceptance criteria testable
- [ ] Implementation feasible

## Recommendations
[Prioritized action items before implementation begins]
```

## Agent coordination

Agents should:

1. **Read the specification thoroughly** before providing feedback
2. **Reference specific sections** with line numbers where possible
3. **Distinguish severity levels**: CRITICAL vs IMPORTANT vs OPTIONAL
4. **Identify positive patterns** worth replicating
5. **Provide actionable recommendations** with clear rationale
6. **Coordinate output** into single review file (not separate files per agent)
