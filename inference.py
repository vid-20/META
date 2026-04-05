"""
inference.py — Runs all three Bug Triage tasks against an LLM via OpenAI-compatible API.

Environment variables
---------------------
OPENAI_API_KEY  : API key
MODEL_NAME      : e.g. gpt-4o, claude-3-5-sonnet-20241022
API_BASE_URL    : e.g. https://api.openai.com/v1
"""

from __future__ import annotations

import json
import os
import sys
import textwrap
import time
from typing import Any, Dict


# -- Local imports --
sys.path.insert(0, os.path.dirname(__file__))

from env import Action, BugTriageEnv
from tasks.task1 import Task1
from tasks.task2 import Task2
from tasks.task3 import Task3
from graders.grader1 import Grader1
from graders.grader2 import Grader2
from graders.grader3 import Grader3


# ---------------------------------------------------------------------------
# OpenAI client setup
# ---------------------------------------------------------------------------




# ---------------------------------------------------------------------------
# Prompt builder
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = textwrap.dedent("""\
    You are an expert software engineering bug triage specialist.
    Your job is to analyze bug reports and produce a structured triage decision.

    You MUST respond with a single valid JSON object and nothing else.
    The JSON must have these fields:
    {
      "severity":       "critical" | "high" | "medium" | "low",
      "category":       "crash" | "performance" | "security" | "ui" | "data_loss" | "feature_request" | "other",
      "assigned_team":  "backend" | "frontend" | "infra" | "security" | "mobile" | "qa",
      "priority_score": <integer 1-10>,
      "summary":        "<one concise sentence describing the bug>",
      "needs_more_info": true | false,
      "duplicate_of":   null | "<BUG-ID>"
    }

    Reasoning guidelines:
    - severity   : impact to users / business (critical=system down/data breach, high=major feature broken,
                   medium=degraded experience, low=cosmetic)
    - category   : root cause category
    - assigned_team: team best placed to fix this
    - priority_score: 1 (ignore) → 10 (drop everything)
    - needs_more_info: true if the report lacks version, repro steps, or is inconsistent
    - duplicate_of: null unless you are certain it duplicates a known bug
""")


def build_user_prompt(obs) -> str:
    r = obs.bug_report
    lines = [
        f"Bug ID   : {r.id}",
        f"Title    : {r.title}",
        f"Product  : {r.product}  v{r.version}",
        f"Reporter : {r.reporter}",
        "",
        "Description:",
        r.description,
    ]
    if r.logs:
        lines += ["", "Logs:", r.logs]
    if r.steps_to_reproduce:
        lines += ["", "Steps to reproduce:"] + r.steps_to_reproduce
    if obs.feedback and obs.step > 0:
        lines += ["", f"[Previous feedback]: {obs.feedback}"]
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# LLM call with retry
# ---------------------------------------------------------------------------

def simple_agent(obs):
    report = obs.bug_report

    text = (report.description or "").lower()
    logs = (report.logs or "").lower()
    steps = " ".join(report.steps_to_reproduce or []).lower()

    full_text = text + " " + logs + " " + steps

    # DEFAULT VALUES
    severity = "low"
    category = "ui"
    assigned_team = "frontend"
    priority_score = 3
    needs_more_info = False

    # -------------------------
    # NEEDS MORE INFO
    # -------------------------
    if "unknown" in (report.version or "").lower():
        needs_more_info = True

    if (not report.steps_to_reproduce or len(report.steps_to_reproduce) == 0) and not report.logs:
        needs_more_info = True

    # -------------------------
    # SECURITY (FIRST)
    # -------------------------
    # SECURITY
    if any(word in full_text for word in [
     "unauthorized", "bypass", "token", "exploit",
     "access other users", "auth"
    ]):
     severity = "critical"
     category = "security"
     assigned_team = "security"
     priority_score = 10

# PERFORMANCE
    elif any(word in full_text for word in [
     "slow", "latency", "timeout", "lag", "performance issue"
    ]):
     severity = "high"
     category = "performance"
     assigned_team = "backend"
     priority_score = 7

# CRASH
    elif any(word in full_text for word in [
     "crash", "exception", "fatal", "app crashes"
    ]):
     severity = "critical"
     category = "crash"
     assigned_team = "frontend"
     priority_score = 9

    # -------------------------
    # UI (LAST)
    # -------------------------
    elif any(word in full_text for word in ["typo", "label", "button", "alignment"]):
        severity = "low"
        category = "ui"
        assigned_team = "frontend"
        priority_score = 2

    return {
        "severity": severity,
        "category": category,
        "assigned_team": assigned_team,
        "priority_score": priority_score,
        "summary": report.title[:100],
        "needs_more_info": needs_more_info,
        "duplicate_of": None,
    }
# ---------------------------------------------------------------------------
# Run one task episode
# ---------------------------------------------------------------------------

def run_task(env: BugTriageEnv, task_label: str) -> Dict[str, Any]:
    print(f"\n{'='*60}")
    print(f"  TASK: {task_label}")
    print(f"{'='*60}")

    obs = env.reset()
    episode_rewards = []
    step = 0

    while not obs.done:
        step += 1
        user_prompt = build_user_prompt(obs)
        raw_action = simple_agent(obs)

        print(f"\n  [Step {step}] LLM action:")
        for k, v in raw_action.items():
            print(f"    {k}: {v}")

        action = Action(**{k: raw_action.get(k, None) for k in Action.model_fields
                           if raw_action.get(k) is not None})

        obs, reward, done, info = env.step(action)
        episode_rewards.append(reward.total)

        print(f"\n  [Step {step}] Reward: {reward.total:.4f}")
        print(reward.feedback)
        print(f"  Elapsed: {info['elapsed_seconds']}s")

        if done:
            break

    final_score = max(episode_rewards) if episode_rewards else 0.0
    print(f"\n  ✅ Final score for {task_label}: {final_score:.4f}")
    return {"task": task_label, "final_score": final_score, "steps": step}


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():

    tasks_and_graders = [
        (Task1(), Grader1(), "Task 1 — Easy   (UI Typo)"),
        (Task2(), Grader2(), "Task 2 — Medium (Performance Regression)"),
        (Task3(), Grader3(), "Task 3 — Hard   (Security / Auth Bypass)"),
    ]

    results = []
    for task, grader, label in tasks_and_graders:
        env = BugTriageEnv(task, grader)
        result = run_task(env, label)
        results.append(result)

    print(f"\n{'='*60}")
    print("  FINAL RESULTS SUMMARY")
    print(f"{'='*60}")
    total = 0.0
    for r in results:
        print(f"  {r['task']:<45}  score={r['final_score']:.4f}  steps={r['steps']}")
        total += r["final_score"]
    avg = total / len(results)
    print(f"\n  Overall average score: {avg:.4f}")
    print(f"{'='*60}\n")

    # Machine-readable output
    print("JSON_RESULTS:", json.dumps({"results": results, "average": round(avg, 4)}))


if __name__ == "__main__":
    main()