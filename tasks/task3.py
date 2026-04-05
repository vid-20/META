"""
Task 3 — HARD
A potential security vulnerability with cryptic logs, incomplete report,
and cross-team ownership ambiguity. Agent must also flag need_for_more_info
correctly and assign to security team.
Expected triage: severity=critical, category=security, team=security, priority=10
"""

from __future__ import annotations
from env import BugReport


TASK_ID = "task3"


class Task3:
    task_id = TASK_ID
    difficulty = "hard"
    description = (
        "Triage a report that hints at an authentication bypass. "
        "The report is incomplete, logs are cryptic, and the agent must "
        "correctly identify this as a critical security issue while flagging "
        "that more information is required."
    )

    expected = {
        "severity":      "critical",
        "category":      "security",
        "assigned_team": "security",
        "priority_score_range": (9, 10),
        "needs_more_info": True,   # report is incomplete — flag required
    }

    def bug_report(self) -> BugReport:
        return BugReport(
            id="BUG-317",
            title="Can access other users' data after session token manipulation",
            description=(
                "I was testing our mobile app and noticed that if I modify the "
                "Authorization header value slightly (flipping a few chars) I "
                "sometimes get a 200 response with *another user's* profile data "
                "instead of a 401. This happened twice but I cannot reproduce it "
                "consistently. I don't know which endpoint exactly. "
                "Could be a caching issue? Or maybe token validation is broken."
            ),
            reporter="security-bounty-external@protonmail.com",
            product="Mobile API",
            version="unknown",
            logs=(
                "[WARN]  2024-03-12T09:11:44Z  auth_middleware: JWT decode soft-fail, "
                "falling through to legacy token check\n"
                "[INFO]  2024-03-12T09:11:44Z  user_service: resolved user_id=8821 "
                "from request context\n"
                "[INFO]  2024-03-12T09:11:44Z  profile_controller: returning profile "
                "for user_id=8821\n"
                "[WARN]  2024-03-12T09:11:44Z  audit_log: request user context "
                "mismatch — token_user=9042 resolved_user=8821"
            ),
            steps_to_reproduce=[
                "1. Authenticate as a normal user and capture the Authorization header.",
                "2. Alter one or more characters in the token.",
                "3. Re-send a GET /api/profile request with the modified token.",
                "4. Observe that sometimes a 200 is returned with another user's data.",
            ],
        )