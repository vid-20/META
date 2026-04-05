from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional, List

app = FastAPI()

# -----------------------------
# Data Models
# -----------------------------

class BugReport(BaseModel):
    id: str
    title: str
    description: str
    product: Optional[str] = ""
    version: Optional[str] = ""
    reporter: Optional[str] = ""
    logs: Optional[str] = ""
    steps_to_reproduce: Optional[List[str]] = []


class Observation(BaseModel):
    bug_report: BugReport


# -----------------------------
# Agent Logic (YOUR FINAL ONE)
# -----------------------------

def simple_agent(report: BugReport):
    text = (report.description or "").lower()
    logs = (report.logs or "").lower()
    steps = " ".join(report.steps_to_reproduce or []).lower()

    full_text = text + " " + logs + " " + steps

    severity = "low"
    category = "ui"
    assigned_team = "frontend"
    priority_score = 3
    needs_more_info = False

    if "unknown" in (report.version or "").lower():
        needs_more_info = True

    if not report.steps_to_reproduce:
        needs_more_info = True

    if "typo" in full_text or "label" in full_text:
        severity = "low"
        category = "ui"
        assigned_team = "frontend"
        priority_score = 2

    elif any(word in full_text for word in [
        "slow", "latency", "timeout", "lag",
        "query", "db", "database", "performance"
    ]):
        severity = "high"
        category = "performance"
        assigned_team = "backend"
        priority_score = 7

    elif any(word in full_text for word in [
        "auth", "token", "unauthorized", "bypass", "access", "login"
    ]):
        severity = "critical"
        category = "security"
        assigned_team = "security"
        priority_score = 9
        needs_more_info = True

    return {
        "severity": severity,
        "category": category,
        "assigned_team": assigned_team,
        "priority_score": priority_score,
        "summary": "Auto triaged bug",
        "needs_more_info": needs_more_info,
        "duplicate_of": None,
    }


# -----------------------------
# API ROUTES
# -----------------------------

@app.post("/reset")
def reset():
    return {"status": "ok"}


@app.post("/step")
def step(obs: Observation):
    action = simple_agent(obs.bug_report)
    return action