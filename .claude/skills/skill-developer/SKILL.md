---
name: skill-developer
description: Meta-skill for creating and managing Claude Code skills. Activated when creating skills, modifying skill rules, or working with the skill system.
---

# Skill developer

## Purpose

Guide for creating and managing Claude Code skills. Covers skill structure, triggers, rules configuration, and best practices.

## When to use

This skill activates when:

- Creating new skills
- Modifying existing skills
- Configuring skill triggers
- Understanding the skill system
- Debugging skill activation

## Skill structure

### Directory layout

```text
.claude/skills/
├── skill-rules.json          # Skill activation rules
└── my-skill/
    └── SKILL.md              # Skill content
```

### SKILL.md format

```markdown
---
name: my-skill
description: Brief description for skill activation. Keywords here help trigger the skill.
---

# Skill title

## Purpose

What this skill is for and when to use it.

## When to use

This skill activates when:

- Condition 1
- Condition 2

## Core content

[Skill-specific guidance]

## Checklist

- [ ] Verification item 1
- [ ] Verification item 2
```

## skill-rules.json

### Basic structure

```json
{
  "version": "1.0.0",
  "skills": {
    "my-skill": {
      "type": "domain",
      "enforcement": "suggest",
      "priority": "high",
      "description": "What this skill does",
      "promptTriggers": {
        "keywords": ["keyword1", "keyword2"],
        "intentPatterns": ["pattern.*match"]
      }
    }
  }
}
```

### Fields

| Field | Values | Description |
|-------|--------|-------------|
| type | "domain", "guardrail" | Skill category |
| enforcement | "suggest", "warn", "block" | How strongly to recommend |
| priority | "critical", "high", "medium", "low" | Display priority |

### Prompt triggers

```json
"promptTriggers": {
  "keywords": [
    "exact match word",
    "another keyword"
  ],
  "intentPatterns": [
    "(create|write).*?test",
    "how.*?implement"
  ]
}
```

### File triggers

```json
"fileTriggers": {
  "paths": [
    "**/*.py",
    "**/tests/**",
    "**/pyproject.toml"
  ]
}
```

### Content triggers

```json
"contentTriggers": {
  "patterns": [
    "@dataclass",
    "from typing import",
    "def test_"
  ]
}
```

## Creating a new skill

### 1. Create directory

```bash
mkdir -p .claude/skills/my-skill
```

### 2. Create SKILL.md

Write the skill content with frontmatter.

### 3. Add to skill-rules.json

Add entry with appropriate triggers.

### 4. Test activation

Try prompts that should trigger the skill.

## Best practices

### Skill scope

- One skill per domain/concept
- Clear, focused purpose
- Not too broad, not too narrow

### Keywords

- Include common terms users would use
- Include technical terms
- Include synonyms

### Intent patterns

- Use regex for flexible matching
- Match user intent, not specific phrasing
- Test with various phrasings

### Content

- Actionable guidance
- Code examples
- Checklists for verification
- Links to external resources

## Example skill

### SKILL.md

```markdown
---
name: api-design
description: API design patterns and best practices for Python APIs.
---

# API design

## Purpose

Guide for designing clean, type-safe Python APIs.

## When to use

This skill activates when:

- Designing public interfaces
- Creating function signatures
- Building class APIs

## Core principles

### Type-safe signatures

\`\`\`python
def process(
    data: list[str],
    *,
    strict: bool = False,
) -> Result:
    ...
\`\`\`

## Checklist

- [ ] All parameters typed
- [ ] Return type specified
- [ ] Keyword-only args for options
```

### skill-rules.json entry

```json
"api-design": {
  "type": "domain",
  "enforcement": "suggest",
  "priority": "high",
  "description": "API design patterns and best practices",
  "promptTriggers": {
    "keywords": ["api design", "function signature", "public interface"],
    "intentPatterns": ["(design|create).*?api", "how.*?signature"]
  },
  "fileTriggers": {
    "paths": ["**/src/**/__init__.py"]
  }
}
```

## Debugging

### Check if skill triggers

1. Look for skill activation message in output
2. Verify keywords match your prompt
3. Test intent patterns with regex tester

### Common issues

- Keywords too specific (not matching)
- Patterns too broad (matching everything)
- Priority too low (not shown)

## Checklist

- [ ] SKILL.md has proper frontmatter
- [ ] Description includes trigger keywords
- [ ] skill-rules.json entry added
- [ ] Triggers tested with sample prompts
- [ ] Content is actionable and complete

---

**Related files:**

- `.claude/skills/skill-rules.json` - Activation rules
- `.claude/hooks/skill_activation_prompt.py` - Activation hook
