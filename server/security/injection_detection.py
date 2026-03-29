"""Utilities for detecting potential prompt injection attempts in user input.

This is for logging and monitoring suspicious patterns, not for blocking requests.
The system prompt hardening is the primary defense.
"""

import re
from typing import Any

# Common prompt injection red flags
INJECTION_PATTERNS = [
    # Instruction overrides
    r"ignore.*(?:previous|all).*instructions?",
    r"disregard.*instructions?",
    r"forget.*(?:your|previous).*instructions?",
    # Role-play / persona changes
    r"(?:act|behave|pretend|roleplay)\s+(?:as|like)",
    r"you\s+(?:are|will\s+be)\s+(?:now|from\s+now)\s+(?:a|an)",
    # Data extraction attempts
    r"(?:repeat|output|show|display|reveal).*(?:full|complete|entire|whole).*(?:background|narrative|prompt)",
    r"tell\s+me\s+(?:what|about)",
    # Conflicting instructions
    r"(?:confirm|verify|acknowledge)\s+you\s+understand\s+by",
    # General conversation prompts
    r"(?:have\s+a\s+conversation|chat\s+with\s+me|discuss|let\'s\s+talk)",
]


def detect_injection_patterns(text: str) -> list[str]:
    """Scan text for common prompt injection patterns.

    Returns a list of matched patterns (empty if none found).
    """
    if not text:
        return []

    text_lower = text.lower()
    matches = []

    for pattern in INJECTION_PATTERNS:
        if re.search(pattern, text_lower, re.IGNORECASE):
            matches.append(pattern)

    return matches


def log_suspicious_jd(jd_content: str, user_id: str, patterns: list[str]) -> None:
    """Log a JD that contains suspicious patterns.

    This is informational — the system prompt provides the actual defense.
    """
    if not patterns:
        return

    # In a real app, this would write to a structured log (Cloud Logging, DataDog, etc.)
    # For now, just print for development visibility
    print(
        f"[SECURITY] Suspicious JD detected for user {user_id}. "
        f"Matched {len(patterns)} pattern(s): {', '.join(patterns[:3])}"
    )


def analyze_jd_for_injection(jd_content: str, user_id: str) -> dict[str, Any]:
    """Analyze a JD for injection attempts. Returns a report (non-blocking).

    Returns:
        {
            "risk_level": "low" | "medium" | "high",
            "suspicious_patterns": ["pattern1", "pattern2", ...],
            "pattern_count": int,
        }
    """
    patterns = detect_injection_patterns(jd_content)

    if not patterns:
        risk_level = "low"
    elif len(patterns) == 1:
        risk_level = "medium"
    else:
        risk_level = "high"

    if risk_level in ("medium", "high"):
        log_suspicious_jd(jd_content, user_id, patterns)

    return {
        "risk_level": risk_level,
        "suspicious_patterns": patterns,
        "pattern_count": len(patterns),
    }
