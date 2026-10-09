
# TaskSentinel — QA Test Automation Framework & System

> An end-to-end QA automation framework featuring Pytest API testing, Playwright UI automation, self-contained HTML execution reporting, and an autonomous AI triage sentinel that auto-files structured defects into a live full-stack system.

[![Python](https://img.shields.io/badge/Python-3.12-blue?logo=python)](https://www.python.org/)
[![Pytest](https://img.shields.io/badge/Pytest-Test%20Framework-yellow?logo=pytest)](https://pytest.org/)
[![Playwright](https://img.shields.io/badge/Playwright-E2E%20Automation-orange?logo=playwright)](https://playwright.dev/)
[![pytest-html](https://img.shields.io/badge/Reports-pytest--html-green)](https://pypi.org/project/pytest-html/)
[![Groq](https://img.shields.io/badge/AI%20Triage-Groq%20API-red)](https://groq.com/)
[![Django](https://img.shields.io/badge/SUT-Django%206%20%2B%20DRF-092E20?logo=django)](https://www.djangoproject.com/)
[![React](https://img.shields.io/badge/SUT-React%2019%20UI-cyan?logo=react)](https://react.dev/)

---

## QA & Test Strategy Overview

This repository demonstrates modern Quality Engineering practices applied to a real-world, multi-tenant System Under Test (SUT). Instead of running tests against mock servers, the automation suite exercises an integrated stack comprising:
* A **React 19** frontend with interactive Kanban workflows.
* A **Django REST Framework** backend operating on PostgreSQL.
* Real-time **WebSocket** event streams (Django Channels + Redis).

```text
                                  TEST RUNNER (Pytest)
                 ┌──────────────────────────┴──────────────────────────┐
                 ▼                                                     ▼
       [ API Test Suite ]                                    [ UI E2E Test Suite ]
       (Pytest + Requests)                                   (Playwright Browser)
                 │                                                     │
                 ▼                                                     ▼
      Backend REST Endpoints                                React 19 Frontend (SPA)
                 │                                                     │
                 └──────────────────────────┬──────────────────────────┘
                                            │
                                    [ Assertion Fails ]
                                            ▼
                           [ Autonomous AI QA Sentinel ]
                             - Captures Failure Artifacts
                             - LLM Root-Cause Triage (Groq)
                             - Auto-Files Bug via REST API
                             - Broadcasts Alert over WebSockets
```

---

## Test Automation Architecture

The automation framework lives in the `/automation` directory, decoupled from backend application code:

```text
automation/
├── tests/
│   ├── test_defect_api.py       # API functional, contract, and permission tests
│   ├── test_kanban_ui.py        # Playwright E2E browser automation (Chromium)
│   └── test_sentinel_trigger.py # Hook verification for automated defect filing
├── reports/                     # Standalone HTML execution reports & failure screenshots
│   ├── api-test-report.html     # Bundled pytest-html execution dashboard
│   └── screenshots/             # Visual failure captures taken by Playwright
├── conftest.py                  # Pytest fixtures, hookimpl failure listener, AI triage client
└── .env                         # Test credentials and LLM configuration
```

---

## Test Suites & Coverage

### 1. API Functional & Contract Testing (`test_defect_api.py`)
* **Authentication & Authorization:** Verifies that unauthenticated requests receive `401 Unauthorized` and cross-tenant actions return `403 Forbidden`.
* **Defect Schema Validation:** Validates that bug creations persist defect-specific metadata (`issue_type="BUG"`, `severity`, `steps_to_reproduce`, `expected_behavior`, `actual_behavior`, `environment`).
* **Report Export Verification:** Asserts that the Markdown exporter action (`/api/tasks/{id}/export-report/`) returns valid Markdown for external trackers.

### 2. End-to-End Browser Automation (`test_kanban_ui.py`)
* **Session Management:** Automates login through the React UI and validates route transitions away from `/login`.
* **SPA Synchronization:** Uses Playwright's web-first assertions (`expect(page).not_to_have_url(...)`) to avoid brittle static sleeps during client-side route changes.
* **Kanban Interaction:** Navigates to project boards, waits for remote database loading states to resolve, verifies column layout (`To Do`, `In Progress`, `Done`), and creates issues via modal forms.

---

## The Autonomous QA Sentinel (AI Defect Triage)

The framework includes an autonomous defect capture pipeline implemented in `automation/conftest.py` using `pytest_runtest_makereport`:

```text
 1. Pytest executes automated test
               │
               ▼
       [ Assertion Fails ]
               │
               ▼
 2. Failure Hook intercepts execution:
    - Captures browser screenshot via Playwright (.png)
    - Extracts stack trace and assertion details
               │
               ▼
 3. Groq LLM Triage (Dynamic Model Discovery):
    - Reads error trace and screenshot metadata
    - Generates actionable defect title (under 80 chars)
    - Formats numbered steps to reproduce
    - Calculates severity (CRITICAL, MAJOR, MINOR)
               │
               ▼
 4. Auto-files ticket via REST API (POST /api/tasks/):
    - Populates database record with issue_type="BUG"
               │
               ▼
 5. Live WebSocket Event:
    - Real-time alert broadcasts to connected project dashboards
```

### Resiliency & Fallback
If the LLM endpoint experiences rate limits or network issues, the hook automatically engages a **rule-based fallback** so that defect tickets are still submitted without crashing the test runner.

---

## QA Reporting Artifacts

* **Self-Contained HTML Dashboards:** Generated via `pytest-html` with `--self-contained-html`. CSS, JavaScript, and test metadata are bundled into a single file (`api-test-report.html`) for review without external assets.
* **Visual Failure Evidence:** When a browser-based test fails, Playwright takes a full-page screenshot stored in `reports/screenshots/` and associates it with the test ID.
* **Defect Markdown Export:** Tasks marked as `BUG` provide a dedicated endpoint returning formatted Markdown ready for Jira or GitHub Issues:
  ```markdown
  # [BUG-14] Task status remains TODO instead of DONE
  **Severity:** CRITICAL | **Priority:** HIGH
  **Environment:** Pytest / Playwright Automated Test Runner
  
  ### Steps to Reproduce
  1. Execute automated test 'test_deliberate_failure_for_qa_sentinel'.
  2. Trigger status transition assertion.
  
  ### Actual Behavior
  AssertionError: Expected task status 'DONE', but got 'TODO'
  ```

---

## Running the Tests Locally

### Prerequisites
* Python 3.12+ with [`uv`](https://github.com/astral-sh/uv)
* Node.js 18+ and `npm`
* Redis Server running on port `6379`
* PostgreSQL database instance

---

### 1. Start the Application Under Test (SUT)

#### Backend (Django + Channels):
```bash
cd backend
uv sync
uv run python manage.py migrate
uv run python manage.py loaddata fixtures/test_data.json
uv run python manage.py runserver
```
*Backend active at `http://127.0.0.1:8000`*

#### Frontend (React + Vite):
```bash
cd frontend
npm install
npm run dev
```
*Frontend active at `http://localhost:5173`*

---

### 2. Configure Test Environment

Create an `.env` file in the `/automation` folder:

```env
TASK_MANAGER_BASE_URL=http://127.0.0.1:8000
FRONTEND_BASE_URL=http://localhost:5173
GROQ_API_KEY=gsk_your_groq_api_key_here
```

---

### 3. Execute the Automation Suites

From the `backend/` directory:

```bash
# 1. Run API Test Suite with Standalone HTML Report
uv run pytest ../automation/tests/test_defect_api.py \
  --html=../automation/reports/api-test-report.html \
  --self-contained-html

# 2. Run Playwright E2E Browser Tests in Headed Mode
uv run pytest ../automation/tests/test_kanban_ui.py --headed -s

# 3. Verify the Autonomous AI Triage Sentinel (Intentional Failure Hook)
uv run pytest ../automation/tests/test_sentinel_trigger.py -s
```

---

## Defect Lifecycle Standards

This framework adheres to the following defect classification matrix:

| Severity | Definition | Example Scenario |
| :--- | :--- | :--- |
| **CRITICAL** | Core workflow blocked; authentication failure; data corruption. | Unable to log in; task status changes fail to persist (HTTP 500). |
| **MAJOR** | Major feature broken without simple workaround. | Project member list fails to load on the Kanban board. |
| **MINOR** | Functional defect with an available workaround. | Status filter dropdown ordering is inconsistent. |
| **TRIVIAL** | Cosmetic or layout defect. | Alignment issues in card badges. |

---

```
