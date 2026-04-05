"""
Grader for Task 2 (Medium — performance regression).

Scoring dimensions
------------------
- severity      : 0.25 pts  (must be 'high'; 'critical' gets partial)
- category      : 0.25 pts  (must be 'performance')
- assigned_team : 0.20 pts  (must be 'backend')
- priority_score: 0.15 pts  (range 6–9)
- summary       : 0.10 pts  (keywords: latency/slow/performance/query/cache/timeout)
- needs_more_info: 0.05 pts (should be False — enough info exists)
Total possible  : 1.00
"""

from __future__ import annotations
from env import Action, Reward


class Grader2:
    KEYWORDS = {"latency", "slow", "performance", "query", "cache", "timeout",
                "regression", "degraded", "api", "dashboard"}

    def grade(self, action: Action, task) -> Reward:
        breakdown: dict[str, float] = {}

        # Severity
        if action.severity == "high":
            breakdown["severity"] = 0.25
        elif action.severity == "critical":
            breakdown["severity"] = 0.15  # overcalled but understandable
        elif action.severity == "medium":
            breakdown["severity"] = 0.08
        else:
            breakdown["severity"] = 0.0

        # Category
        breakdown["category"] = 0.25 if action.category == "performance" else 0.0

        # Team
        if action.assigned_team == "backend":
            breakdown["assigned_team"] = 0.20
        elif action.assigned_team == "infra":
            breakdown["assigned_team"] = 0.10  # reasonable but not best
        else:
            breakdown["assigned_team"] = 0.0

        # Priority score (range 6–9)
        lo, hi = task.expected["priority_score_range"]
        if lo <= action.priority_score <= hi:
            breakdown["priority_score"] = 0.15
        elif action.priority_score == 10:
            breakdown["priority_score"] = 0.07  # slight overestimate
        elif action.priority_score >= 4:
            breakdown["priority_score"] = 0.05
        else:
            breakdown["priority_score"] = 0.0

        # Summary quality
        summary_lower = action.summary.lower()
        hits = sum(1 for kw in self.KEYWORDS if kw in summary_lower)
        breakdown["summary"] = round(min(hits / 3, 1.0) * 0.10, 4)

        # needs_more_info — logs + reproduction steps are sufficient → should be False
        breakdown["needs_more_info"] = 0.05 if not action.needs_more_info else 0.0

        total = round(sum(breakdown.values()), 4)
        feedback = self._build_feedback(action, breakdown)
        return Reward(total=total, breakdown=breakdown, penalties={}, feedback=feedback)

    @staticmethod
    def _build_feedback(action: Action, breakdown: dict) -> str:
        lines = ["=== Grader 2 Feedback (Medium) ==="]
        for dim, score in breakdown.items():
            lines.append(f"  {dim}: {score:.2f}")
        if action.category != "performance":
            lines.append("  ✗ Logs clearly show slow DB queries — category should be 'performance'.")
        if action.assigned_team not in {"backend", "infra"}:
            lines.append("  ✗ No frontend changes in v3.5.0 — backend/infra owns this.")
        if action.needs_more_info:
            lines.append("  ✗ Sufficient logs and repro steps exist; more info not needed.")
        return "\n".join(lines)