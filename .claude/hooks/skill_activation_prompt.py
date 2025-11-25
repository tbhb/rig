#!/usr/bin/env -S uv run --script
"""Hook to check user prompts for skill activation triggers.

This hook runs on prompt submission and checks if any configured skills
should be activated based on keyword or intent pattern matching.
"""

import json
import os
import re
import sys
from pathlib import Path
from typing import Literal, TypedDict, cast

from rich.console import Console

_console = Console()
_err_console = Console(stderr=True)


class PromptTriggers(TypedDict, total=False):
    """Trigger configuration for skill activation."""

    keywords: list[str] | None
    intentPatterns: list[str] | None


class SkillRule(TypedDict):
    """Configuration for a single skill rule."""

    type: Literal["guardrail", "domain"]
    enforcement: Literal["block", "suggest", "warn"]
    priority: Literal["critical", "high", "medium", "low"]
    promptTriggers: PromptTriggers | None


class SkillRules(TypedDict):
    """Container for all skill rules."""

    version: str
    skills: dict[str, SkillRule]


class HookInput(TypedDict):
    """Input data provided to the hook via stdin."""

    session_id: str
    transcript_path: str
    cwd: str
    permission_mode: str
    prompt: str


class MatchedSkill(TypedDict):
    """A skill that matched the user's prompt."""

    name: str
    matchType: Literal["keyword", "intent"]
    config: SkillRule


def _load_skill_rules(project_dir: Path) -> SkillRules | None:
    """Load skill rules from the project configuration.

    Args:
        project_dir: Root directory of the project.

    Returns:
        Parsed skill rules or None if file doesn't exist.
    """
    rules_path = project_dir / ".claude" / "skills" / "skill-rules.json"
    if not rules_path.exists():
        return None
    with rules_path.open("r", encoding="utf-8") as f:
        return cast("SkillRules", json.load(f))


def _match_skill(
    skill_name: str, config: SkillRule, prompt: str
) -> MatchedSkill | None:
    """Check if a skill matches the given prompt.

    Args:
        skill_name: Name of the skill to check.
        config: Skill configuration with triggers.
        prompt: User prompt to match against (lowercase).

    Returns:
        MatchedSkill if matched, None otherwise.
    """
    triggers = config.get("promptTriggers")
    if not triggers:
        return None

    # Keyword matching
    keywords = triggers.get("keywords")
    if keywords and any(kw.lower() in prompt for kw in keywords):
        return {"name": skill_name, "matchType": "keyword", "config": config}

    # Intent pattern matching
    intent_patterns = triggers.get("intentPatterns")
    if intent_patterns:
        for pattern in intent_patterns:
            if re.search(pattern, prompt, re.IGNORECASE):
                return {"name": skill_name, "matchType": "intent", "config": config}

    return None


def _group_by_priority(
    matched_skills: list[MatchedSkill],
) -> dict[str, list[MatchedSkill]]:
    """Group matched skills by their priority level.

    Args:
        matched_skills: List of matched skills to group.

    Returns:
        Dictionary mapping priority levels to skill lists.
    """
    critical = [s for s in matched_skills if s["config"]["priority"] == "critical"]
    high = [s for s in matched_skills if s["config"]["priority"] == "high"]
    medium = [s for s in matched_skills if s["config"]["priority"] == "medium"]
    low = [s for s in matched_skills if s["config"]["priority"] == "low"]
    return {"critical": critical, "high": high, "medium": medium, "low": low}


def _format_skill_list(skills: list[MatchedSkill], header: str) -> str:
    """Format a list of skills with a header.

    Args:
        skills: List of skills to format.
        header: Header text to display.

    Returns:
        Formatted string or empty string if no skills.
    """
    if not skills:
        return ""
    lines = [f"{header}:"]
    lines.extend(f"  → {s['name']}" for s in skills)
    lines.append("")
    return "\n".join(lines)


def _format_output(matched_skills: list[MatchedSkill]) -> str:
    """Format the output message for matched skills.

    Args:
        matched_skills: List of matched skills.

    Returns:
        Formatted output string.
    """
    grouped = _group_by_priority(matched_skills)

    parts = [
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        "🎯 SKILL ACTIVATION CHECK",
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        "",
    ]

    critical_header = "⚠️ CRITICAL SKILLS (REQUIRED)"
    parts.append(_format_skill_list(grouped["critical"], critical_header))
    parts.append(_format_skill_list(grouped["high"], "📚 RECOMMENDED SKILLS"))
    parts.append(_format_skill_list(grouped["medium"], "💡 SUGGESTED SKILLS"))
    parts.append(_format_skill_list(grouped["low"], "📌 OPTIONAL SKILLS"))

    parts.extend(
        [
            "ACTION: Use Skill tool BEFORE responding",
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        ]
    )

    return "\n".join(part for part in parts if part)


def main() -> None:
    """Check user prompt for skill activation triggers and output recommendations."""
    # Read input from stdin
    input_data = sys.stdin.read()
    data = cast("HookInput", json.loads(input_data))
    prompt = data["prompt"].lower()

    # Load skill rules
    project_dir = Path(
        os.environ.get("CLAUDE_PROJECT_DIR", Path(__file__).parent.parent.parent)
    )
    rules = _load_skill_rules(project_dir)
    if rules is None:
        return

    # Check each skill for matches
    matched_skills: list[MatchedSkill] = []
    for skill_name, config in rules["skills"].items():
        match = _match_skill(skill_name, config, prompt)
        if match:
            matched_skills.append(match)

    # Output recommendations if any skills matched
    if matched_skills:
        output = _format_output(matched_skills)
        _console.print(output)


if __name__ == "__main__":
    try:
        main()
    except (json.JSONDecodeError, KeyError, OSError) as err:
        _err_console.print(f"Error in skill-activation-prompt hook: {err}")
        sys.exit(1)
