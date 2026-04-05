"""
Task 2 — MEDIUM
A performance regression bug with partial logs and ambiguous component ownership.
Expected triage: severity=high, category=performance, team=backend, priority=7
"""

from __future__ import annotations
from env import BugReport


TASK_ID = "task2"


class Task2:
    task_id = TASK_ID
    difficulty = "medium"
    description = (
        "Triage a reported API latency regression introduced after a recent deploy. "
        "Logs are provided but team ownership requires reasoning about the stack."
    )

    expected = {
        "severity":      "high",
        "category":      "performance",
        "assigned_team": "backend",
        "priority_score_range": (6, 9),
        "needs_more_info": False,
    }

    def bug_report(self) -> BugReport:
        return BugReport(
            id="BUG-042",
            title="Dashboard API response time degraded 5× after v3.5.0 deploy",
            description=(
                "Since the production deployment of v3.5.0 on 2024-03-10, "
                "the /api/dashboard endpoint has gone from ~120 ms average "
                "response time to ~600 ms. Approximately 30 % of users are "
                "experiencing timeouts (>2 s). Revenue dashboards are affected. "
                "No frontend changes were included in v3.5.0 — only backend "
                "service updates. The issue does not reproduce in staging."
            ),
            reporter="oncall-eng@example.com",
            product="Analytics Platform",
            version="3.5.0",
            logs=(
                "[ERROR] 2024-03-10T14:22:01Z  db_query_executor: slow query detected "
                "(2341 ms) — SELECT * FROM events WHERE user_id=? AND ts > ?\n"
                "[WARN]  2024-03-10T14:22:05Z  api_gateway: upstream timeout after 2000ms\n"
                "[INFO]  2024-03-10T14:22:05Z  cache_layer: cache MISS ratio 94% "
                "(expected <20%)\n"
                "[ERROR] 2024-03-10T14:23:11Z  db_query_executor: slow query detected "
                "(3102 ms) — SELECT * FROM events WHERE user_id=? AND ts > ?"
            ),
            steps_to_reproduce=[
                "1. Open the Analytics Platform dashboard as any enterprise user.",
                "2. Observe the loading spinner — request takes >1 s.",
                "3. Check network tab: /api/dashboard returns 200 but after ~600 ms+.",
            ],
        )