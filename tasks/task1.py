"""
Task 1 — EASY
A straightforward UI bug with complete reproduction steps.
Expected triage: severity=low, category=ui, team=frontend, priority=2
"""

from __future__ import annotations
from env import BugReport


TASK_ID = "task1"


class Task1:
    task_id = TASK_ID
    difficulty = "easy"
    description = (
        "Triage a simple UI cosmetic bug: a button label is misspelled "
        "on the settings page. All reproduction steps are provided."
    )

    # Ground-truth triage (used by grader)
    expected = {
        "severity":      "low",
        "category":      "ui",
        "assigned_team": "frontend",
        "priority_score_range": (1, 3),   # acceptable 1–3
        "needs_more_info": False,
    }

    def bug_report(self) -> BugReport:
        return BugReport(
            id="BUG-001",
            title='Settings page "Sav" button has typo — should be "Save"',
            description=(
                "On the Account Settings page the primary action button displays "
                '"Sav" instead of "Save". This is a cosmetic issue only; '
                "clicking the button still saves correctly."
            ),
            reporter="alice@example.com",
            product="WebApp",
            version="3.4.1",
            logs=None,
            steps_to_reproduce=[
                "1. Log in with any account.",
                "2. Navigate to Account → Settings.",
                "3. Observe the primary button label at the bottom of the form.",
            ],
        )