"""
OpenEnv: Bug Triage System
Simulates a real-world software bug triage workflow.
"""

from __future__ import annotations

import time
from typing import Any, Dict, List, Optional, Tuple

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Typed Models
# ---------------------------------------------------------------------------

class BugReport(BaseModel):
    """Raw bug report submitted by a user or automated system."""
    id: str
    title: str
    description: str
    reporter: str
    product: str
    version: str
    logs: Optional[str] = None
    steps_to_reproduce: Optional[List[str]] = None


class Observation(BaseModel):
    """What the agent sees at each step."""
    bug_report: BugReport
    step: int
    max_steps: int
    history: List[Dict[str, Any]] = Field(default_factory=list)
    feedback: Optional[str] = None
    done: bool = False


class Action(BaseModel):
    """
    Agent's triage decision.

    Fields
    ------
    severity   : 'critical' | 'high' | 'medium' | 'low'
    category   : 'crash' | 'performance' | 'security' | 'ui' | 'data_loss' | 'feature_request' | 'other'
    assigned_team : 'backend' | 'frontend' | 'infra' | 'security' | 'mobile' | 'qa'
    priority_score: 1–10  (10 = highest)
    summary    : one-sentence summary of the bug
    needs_more_info: bool  (flag for incomplete reports)
    duplicate_of: Optional bug ID this might duplicate
    """
    severity: str
    category: str
    assigned_team: str
    priority_score: int = Field(ge=1, le=10)
    summary: str
    needs_more_info: bool = False
    duplicate_of: Optional[str] = None


class Reward(BaseModel):
    """Structured reward signal."""
    total: float = Field(ge=0.0, le=1.0)
    breakdown: Dict[str, float]
    penalties: Dict[str, float]
    feedback: str


# ---------------------------------------------------------------------------
# Environment
# ---------------------------------------------------------------------------

VALID_SEVERITIES   = {"critical", "high", "medium", "low"}
VALID_CATEGORIES   = {"crash", "performance", "security", "ui", "data_loss", "feature_request", "other"}
VALID_TEAMS        = {"backend", "frontend", "infra", "security", "mobile", "qa"}


class BugTriageEnv:
    """
    OpenEnv-compatible Bug Triage environment.

    Lifecycle
    ---------
    env = BugTriageEnv(task)
    obs = env.reset()
    obs, reward, done, info = env.step(action)
    """

    MAX_STEPS = 3  # agent may refine its triage up to 3 times

    def __init__(self, task, grader):
        self.task   = task
        self.grader = grader
        self._step_count    = 0
        self._history: List[Dict[str, Any]] = []
        self._last_action: Optional[Action] = None
        self._done = False
        self._start_time = time.time()

    # ------------------------------------------------------------------
    # OpenEnv interface
    # ------------------------------------------------------------------

    def reset(self) -> Observation:
        """Return the initial observation for the task."""
        self._step_count = 0
        self._history    = []
        self._last_action = None
        self._done = False
        self._start_time = time.time()

        return Observation(
            bug_report=self.task.bug_report(),
            step=0,
            max_steps=self.MAX_STEPS,
            history=[],
            feedback="New bug report received. Please triage it.",
            done=False,
        )

    def step(self, action: Action) -> Tuple[Observation, Reward, bool, Dict[str, Any]]:
        """
        Process one triage action.

        Returns
        -------
        (observation, reward, done, info)
        """
        if self._done:
            raise RuntimeError("Episode is done. Call reset() first.")

        # --- Validation penalties ----------------------------------------
        penalties: Dict[str, float] = {}

        if action.severity not in VALID_SEVERITIES:
            penalties["invalid_severity"] = 0.15
        if action.category not in VALID_CATEGORIES:
            penalties["invalid_category"] = 0.15
        if action.assigned_team not in VALID_TEAMS:
            penalties["invalid_team"] = 0.10

        # Repeated identical action penalty
        if self._last_action and self._actions_identical(action, self._last_action):
            penalties["repeated_action"] = 0.10

        # --- Grade the action --------------------------------------------
        raw_reward: Reward = self.grader.grade(action, self.task)

        # Apply penalties
        total_penalty = min(sum(penalties.values()), 0.40)
        final_score   = max(0.0, raw_reward.total - total_penalty)
        final_score   = round(final_score, 4)

        reward = Reward(
            total=final_score,
            breakdown=raw_reward.breakdown,
            penalties=penalties,
            feedback=raw_reward.feedback,
        )

        self._step_count  += 1
        self._last_action  = action
        self._history.append({
            "step":   self._step_count,
            "action": action.model_dump(),
            "reward": reward.model_dump(),
        })

        # Done when max steps reached OR agent submits confident triage
        done = (
            self._step_count >= self.MAX_STEPS
            or final_score >= 0.90
            or action.needs_more_info  # agent decided it needs more info → terminal
        )
        self._done = done

        obs = Observation(
            bug_report=self.task.bug_report(),
            step=self._step_count,
            max_steps=self.MAX_STEPS,
            history=list(self._history),
            feedback=reward.feedback,
            done=done,
        )

        info = {
            "elapsed_seconds": round(time.time() - self._start_time, 2),
            "penalties":       penalties,
            "step":            self._step_count,
        }

        return obs, reward, done, info

    def state(self) -> Dict[str, Any]:
        """Return full internal state (for debugging / evaluation harness)."""
        return {
            "task_id":     self.task.task_id,
            "step":        self._step_count,
            "done":        self._done,
            "history":     self._history,
            "last_action": self._last_action.model_dump() if self._last_action else None,
        }

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _actions_identical(a: Action, b: Action) -> bool:
        return (
            a.severity      == b.severity
            and a.category  == b.category
            and a.assigned_team == b.assigned_team
            and a.priority_score == b.priority_score
        )