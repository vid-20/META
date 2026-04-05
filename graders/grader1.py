"""
Grader for Task 1 (Easy — UI cosmetic bug).

Scoring dimensions
------------------
- severity      : 0.25 pts  (must be 'low')
- category      : 0.25 pts  (must be 'ui')
- assigned_team : 0.25 pts  (must be 'frontend')
- priority_score: 0.15 pts  (must be in [1, 3])
- summary       : 0.10 pts  (must mention 'typo' OR 'button' OR 'label')
Total possible  : 1.00
"""

from __future__ import annotations
from env import Action, Reward


class Grader1:
    KEYWORDS = {"typo", "button", "label", "misspell", "cosmetic", "sav", "save"}

    def grade(self, action: Action, task) -> Reward:
        breakdown: dict[str, float] = {}

        # Severity
        breakdown["severity"] = 0.25 if action.severity == "low" else (
            0.10 if action.severity == "medium" else 0.0
        )

        # Category
        breakdown["category"] = 0.25 if action.category == "ui" else 0.0

        # Team
        breakdown["assigned_team"] = 0.25 if action.assigned_team == "frontend" else 0.0

        # Priority score (acceptable range 1–3)
        lo, hi = task.expected["priority_score_range"]
        if lo <= action.priority_score <= hi:
            breakdown["priority_score"] = 0.15
        elif action.priority_score <= 5:
            breakdown["priority_score"] = 0.07  # partial — at least not marked critical
        else:
            breakdown["priority_score"] = 0.0

        # Summary quality
        summary_lower = action.summary.lower()
        hits = sum(1 for kw in self.KEYWORDS if kw in summary_lower)
        breakdown["summary"] = round(min(hits / 2, 1.0) * 0.10, 4)

        total = round(sum(breakdown.values()), 4)

        feedback = self._build_feedback(action, breakdown)
        return Reward(total=total, breakdown=breakdown, penalties={}, feedback=feedback)

    @staticmethod
    def _build_feedback(action: Action, breakdown: dict) -> str:
        lines = ["=== Grader 1 Feedback (Easy) ==="]
        for dim, score in breakdown.items():
            lines.append(f"  {dim}: {score:.2f}")
        if action.severity != "low":
            lines.append("  ✗ Severity should be 'low' for a cosmetic typo.")
        if action.category != "ui":
            lines.append("  ✗ Category should be 'ui'.")
        if action.assigned_team != "frontend":
            lines.append("  ✗ Button labels are a frontend responsibility.")
        return "\n".join(lines)