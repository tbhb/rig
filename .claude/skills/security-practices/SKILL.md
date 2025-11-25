---
name: security-practices
description: Security best practices for Python development. Activated when working with security concerns, input validation, injection prevention, or threat modeling.
---

# Security practices

## Purpose

Comprehensive guide for security in Python projects including input validation, injection prevention, secure defaults, and threat modeling.

## When to use

This skill activates when:

- Validating user input
- Handling file paths
- Executing system commands
- Working with sensitive data
- Reviewing code for vulnerabilities
- Designing security architecture

## Core principles

### Secure by default

- Default configuration should be the secure configuration
- Require explicit opt-in for less secure behavior
- Validate input at system boundaries

### Defense in depth

- Use multiple layers of validation
- Never rely on a single security control
- Validate at multiple levels

## Input validation

### String input validation

```python
import re

def validate_identifier(value: str) -> str:
    """Validate identifier string."""
    if not value:
        raise ValueError("Identifier cannot be empty")

    if not re.match(r'^[a-zA-Z][a-zA-Z0-9_]*$', value):
        raise ValueError(f"Invalid identifier: {value}")

    if len(value) > 255:
        raise ValueError("Identifier too long")

    return value

def sanitize_for_display(value: str) -> str:
    """Sanitize string for safe display."""
    # Remove control characters
    return ''.join(c for c in value if c.isprintable() or c in '\n\t')
```

### Path validation

```python
from pathlib import Path

def validate_path(user_path: str, allowed_base: Path) -> Path:
    """Validate path is within allowed directory."""
    # Resolve to absolute path
    path = (allowed_base / user_path).resolve()

    # Check path is within allowed base
    if not path.is_relative_to(allowed_base):
        raise ValueError("Path traversal detected")

    return path

def validate_filename(filename: str) -> str:
    """Validate filename is safe."""
    # Check for path separators
    if '/' in filename or '\\' in filename:
        raise ValueError("Invalid filename: contains path separator")

    # Check for special names
    if filename in ('.', '..'):
        raise ValueError("Invalid filename: special directory name")

    # Check for null bytes
    if '\x00' in filename:
        raise ValueError("Invalid filename: contains null byte")

    return filename
```

## Command injection prevention

### Safe command execution

```python
import subprocess
import shlex

def run_safe_command(args: list[str]) -> subprocess.CompletedProcess:
    """Run command safely without shell."""
    # Never use shell=True with user input
    return subprocess.run(
        args,
        capture_output=True,
        text=True,
        timeout=30,
        check=True,
    )

# Good: List of arguments
run_safe_command(['git', 'log', '--oneline', '-n', '10'])

# BAD: Never do this with user input
# subprocess.run(f"git log {user_input}", shell=True)  # DANGEROUS
```

### Quote user input

```python
import shlex

def quote_for_shell(value: str) -> str:
    """Quote value for safe shell usage."""
    return shlex.quote(value)

# Usage
filename = quote_for_shell(user_provided_filename)
```

## Sensitive data handling

### Environment variables

```python
import os

def get_secret(name: str) -> str:
    """Get secret from environment."""
    value = os.environ.get(name)
    if value is None:
        raise ValueError(f"Required secret not set: {name}")
    return value

# Never log secrets
def process_with_secret(data: str) -> None:
    secret = get_secret("API_KEY")
    # Use secret, never print/log it
    result = call_api(data, auth=secret)
```

### Avoid information leakage

```python
class SafeError(Exception):
    """Error with safe message for users."""

    def __init__(self, user_message: str, internal_details: str | None = None):
        super().__init__(user_message)
        self._internal = internal_details

    @property
    def internal_details(self) -> str | None:
        """Details for logging only, never expose to users."""
        return self._internal

def process_request(data: dict) -> Result:
    try:
        return _process_impl(data)
    except DatabaseError as e:
        # Log full error internally
        logger.error(f"Database error: {e}")
        # Return safe message to user
        raise SafeError("Processing failed", str(e)) from e
```

## OWASP considerations

### Injection flaws

- Never interpolate user input into commands
- Use parameterized queries for databases
- Validate and sanitize all input

### Authentication

- Use secure password hashing (bcrypt, argon2)
- Implement rate limiting
- Use secure session management

### Sensitive data exposure

- Never log sensitive data
- Encrypt data at rest and in transit
- Use environment variables for secrets

## Security checklist

Before completing security-sensitive code:

- [ ] All user input validated
- [ ] No command injection vectors
- [ ] No path traversal vectors
- [ ] Secrets not logged or exposed
- [ ] Error messages don't leak internals
- [ ] Using latest dependency versions
- [ ] Following principle of least privilege

## Threat modeling

When designing features, consider:

1. **What could go wrong?** - Identify attack vectors
2. **What are we doing about it?** - Document mitigations
3. **Did we do a good job?** - Verify implementation
4. **Can we do better?** - Continuous improvement

---

**Additional resources:**

- [OWASP Top 10](https://owasp.org/Top10/)
- [Python Security Best Practices](https://python-security.readthedocs.io/)
