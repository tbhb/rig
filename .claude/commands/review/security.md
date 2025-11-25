---
description: Security-focused code review
argument-hint: [files or directories]
---

Use the @agent-code-reviewer agent to perform a **security-focused review** on: $ARGUMENTS

If no files/directories specified, review `src/`.

## Focus areas

- **Input validation**: User input sanitization, boundary checks
- **Injection risks**: Command injection, path traversal, SQL injection
- **Authentication/Authorization**: Access control, privilege escalation
- **Data protection**: Sensitive data handling, encryption
- **Dependencies**: Known vulnerabilities in dependencies
- **Error handling**: Information leakage in error messages
- **Secure defaults**: Principle of least privilege

## OWASP considerations

Review against common vulnerability patterns:

1. Injection flaws
2. Broken authentication
3. Sensitive data exposure
4. Security misconfiguration
5. Using components with known vulnerabilities

## Output

Save to `reviews/security-review-YYYY-MM-DD-HHmmss.md`:

```markdown
# Security review - [Date/Time]

## Scope
[Files reviewed]

## Threat model
[Attack vectors considered]

## Critical vulnerabilities
[MUST fix immediately]

## Security concerns
[Should be addressed]

## Recommendations
[Security improvements]

## Compliance
- [ ] Input validation implemented
- [ ] No injection vulnerabilities
- [ ] Secure error handling
- [ ] Dependencies are current
```
