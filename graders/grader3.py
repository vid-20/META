"""
Grader for Task 3 (Hard — security / auth-bypass).

Scoring dimensions
------------------
- severity      : 0.30 pts  (must be 'critical')
- category      : 0.25 pts  (must be 'security')
- assigned_team : 0.20 pts  (must be 'security')
- priority_score: 0.10 pts  (must be 9 or 10)
- needs_more_info: 0.10 pts (must be True — report is incomplete)
- summary       : 0.05 pts  (keywords: auth/bypass/token/security/user data)
Total possible  : 1.00
"""

from __future__ import annotations
from env import Action, Reward


class Grader3:
    KEYWORDS = {"auth", "bypass", "token", "security", "unauthori", "access",
                "user data", "privilege", "leak", "idor", "jwt"}

    def grade(self, action: Action, task) -> Reward:
        breakdown: dict[str, float] = {}

        # Severity — must be critical for auth bypass
        if action.severity == "critical":
            breakdown["severity"] = 0.30
        elif action.severity == "high":
            breakdown["severity"] = 0.12  # serious underestimation
        else:
            breakdown["severity"] = 0.0

        # Category
        breakdown["category"] = 0.25 if action.category == "security" else 0.0

        # Team
        breakdown["assigned_team"] = 0.20 if action.assigned_team == "security" else 0.0

        # Priority — must be 9 or 10
        if action.priority_score >= 9:
            breakdown["priority_score"] = 0.10
        elif action.priority_score >= 7:
            breakdown["priority_score"] = 0.05
        else:
            breakdown["priority_score"] = 0.0

        # needs_more_info — MUST be True (version unknown, no consistent repro)
        breakdown["needs_more_info"] = 0.10 if action.needs_more_info else 0.0

        # Summary quality
        summary_lower = action.summary.lower()
        hits = sum(1 for kw in self.KEYWORDS if kw in summary_lower)
        breakdown["summary"] = round(min(hits / 2, 1.0) * 0.05, 4)

        total = round(sum(breakdown.values()), 4)
        feedback = self._build_feedback(action, breakdown)
        return Reward(total=total, breakdown=breakdown, penalties={}, feedback=feedback)

    @staticmethod
    def _build_feedback(action: Action, breakdown: dict) -> str:
        lines = ["=== Grader 3 Feedback (Hard) ==="]
        for dim, score in breakdown.items():
            lines.append(f"  {dim}: {score:.2f}")
        if action.severity != "critical":
            lines.append("  ✗ Auth bypass with cross-user data exposure is CRITICAL.")
        if action.category != "security":
            lines.append("  ✗ Token manipulation leading to data exposure → 'security'.")
        if action.assigned_team != "security":
            lines.append("  ✗ Security incidents must be routed to the security team.")
        if not action.needs_more_info:
            lines.append("  ✗ Version is 'unknown' and repro is inconsistent — flag for more info.")
        return "\n".join(lines)