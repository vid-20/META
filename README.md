# 🐛 Bug Triage System — OpenEnv Environment

## Project Overview

The **Bug Triage System** is a production-ready [OpenEnv](https://openenv.ai)
environment that evaluates AI agents on one of the most common, high-stakes
tasks in software engineering: **triaging incoming bug reports**.

An agent receives a structured bug report and must produce a triage decision
that a senior engineer would be proud of — correct severity classification,
right owning team, meaningful priority score, and a flag when the report is
too incomplete to act on.

---

## Real-World Motivation

Every software company faces a flood of bug reports daily. Incorrectly triaged
bugs lead to:

- Security vulnerabilities treated as cosmetic issues (catastrophic)
- Critical regressions deprioritised (costly downtime)
- Wrong teams assigned (wasted developer hours)

A well-calibrated AI triage agent can dramatically reduce Mean Time To
Resolution (MTTR) and prevent high-severity bugs from slipping through.

---

## Observation / Action / Reward Design

### Observation (`Observation`)
| Field        | Type            | Description                                      |
|--------------|-----------------|--------------------------------------------------|
| `bug_report` | `BugReport`     | The full bug report (title, description, logs, repro steps) |
| `step`       | `int`           | Current step within the episode                  |
| `max_steps`  | `int`           | Maximum allowed steps (3)                        |
| `history`    | `list`          | All prior actions and rewards in this episode    |
| `feedback`   | `str`           | Human-readable feedback from the last grader     |
| `done`       | `bool`          | Whether the episode has ended                    |

### Action (`Action`)
| Field             | Type     | Allowed values / range                                        |
|-------------------|----------|---------------------------------------------------------------|
| `severity`        | `str`    | `critical` \| `high` \| `medium` \| `low`                    |
| `category`        | `str`    | `crash` \| `performance` \| `security` \| `ui` \| `data_loss` \| `feature_request` \| `other` |
| `assigned_team`   | `str`    | `backend` \| `frontend` \| `infra` \| `security` \| `mobile` \| `qa` |
| `priority_score`  | `int`    | 1 (lowest) → 10 (highest)                                     |
| `summary`         | `str`    | One-sentence description of the bug                           |
| `needs_more_info` | `bool`   | True if the report is insufficient to act on                  |
| `duplicate_of`    | `str?`   | Bug ID of a known duplicate, or `null`                        |

### Reward (`Reward`)
Scores are in **[0.0, 1.0]** and reflect partial correctness:

| Situation                          | Score contribution      |
|------------------------------------|-------------------------|
| Exact match on severity            | +0.25 – +0.30           |
| Exact match on category            | +0.25                   |
| Correct team assignment            | +0.20 – +0.25           |
| Priority score in correct range    | +0.10 – +0.15           |
| Quality summary with keywords      | up to +0.10             |
| Correct `needs_more_info` flag     | +0.05 – +0.10           |
| Invalid severity / category / team | −0.10 to −0.15 each     |
| Repeated identical action          | −0.10                   |
| Total penalty cap                  | −0.40 maximum           |

---

## Task Descriptions

### Task 1 — Easy: UI Cosmetic Bug (`BUG-001`)
**Bug**: A button label on the Settings page reads "Sav" instead of "Save".  
**Expected triage**: `severity=low`, `category=ui`, `team=frontend`, `priority=1–3`.  
**Challenge**: Avoiding the temptation to over-classify a harmless cosmetic defect.

### Task 2 — Medium: Performance Regression (`BUG-042`)
**Bug**: The `/api/dashboard` endpoint slowed 5× after a backend-only deploy.
Log snippets show slow DB queries and a broken cache layer.  
**Expected triage**: `severity=high`, `category=performance`, `team=backend`, `priority=6–9`.  
**Challenge**: Reading logs to identify root cause and correct owning team.

### Task 3 — Hard: Security / Auth Bypass (`BUG-317`)
**Bug**: A user reports getting another user's profile data by manipulating
their Authorization token. Logs confirm a JWT soft-fail with a user context
mismatch.  
**Expected triage**: `severity=critical`, `category=security`, `team=security`,
`priority=9–10`, `needs_more_info=true`.  
**Challenge**: Recognising the severity of an incomplete security report,
routing it correctly, AND flagging that more information is required.

---

## Grader Explanation

Each task has a dedicated deterministic grader:

| Grader     | Task   | Key differentiator                                     |
|------------|--------|--------------------------------------------------------|
| `Grader1`  | Easy   | Penalises over-classifying cosmetic bugs               |
| `Grader2`  | Medium | Awards partial credit for `infra` team (close but wrong) |
| `Grader3`  | Hard   | Awards `needs_more_info=true` 10 pts; `critical` is mandatory |

All graders:
- Output a float in `[0.0, 1.0]`
- Are fully **deterministic** (no random components)
- Provide **partial credit** — a wrong severity still earns points for a correct category

---

## Setup Instructions

### Prerequisites
- Python 3.10+
- An OpenAI-compatible API key

### Local Setup
```bash
# 1. Clone / place files in project root
cd bug-triage-openenv/

# 2. Create virtual environment
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set environment variables
export OPENAI_API_KEY="sk-..."
export MODEL_NAME="gpt-4o"                        # or any OpenAI-compatible model
export API_BASE_URL="https://api.openai.com/v1"   # default
```

### Run Locally
```bash
python inference.py
```

### Run with Docker
```bash
# Build
docker build -t bug-triage-openenv .

# Run (pass your key at runtime)
docker run --rm \
  -e OPENAI_API_KEY="sk-..." \
  -e MODEL_NAME="gpt-4o" \
  bug-triage-openenv
```

---

## How to Use the Environment Programmatically
```python
from env import BugTriageEnv, Action
from tasks.task1 import Task1
from graders.grader1 import Grader1

env = BugTriageEnv(Task1(), Grader1())
obs = env.reset()

action = Action(
    severity="low",
    category="ui",
    assigned_team="frontend",
    priority_score=2,
    summary="Button label 'Sav' is a cosmetic typo; should be 'Save'.",
    needs_more_info=False,
)

obs, reward, done, info = env.step(action)
print(f"Score: {reward.total}")   # → 1.0
print(reward.feedback)
```

---

## Expected Baseline Output

Running against **GPT-4o** (temperature=0):