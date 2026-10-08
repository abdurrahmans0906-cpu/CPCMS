# CPCMS — Course Project Configuration and Management System

CPCMS is a web application designed for university course project management with a Software Configuration Management (SCM) engineering layer. Faculty organize course projects, define milestones, evaluation criteria, and review schedules; students form teams, author proposals, manage configuration items (CIs), lock baselines, submit and review change requests (CRs) with impact analysis and visual diffs, track GitHub commits and branches, log progress, audit actions, request formal releases, and receive stage-by-stage evaluations.

---

## 1. Core SCM Features & Architecture

* **Configuration Identification**: Strict naming conventions (`CI-001`, `BL-001`, `CR-YYYY-NNN`, `REL-X.Y.Z`). Categorization into requirements, architecture, design, backend, frontend, test reports, and documentation.
* **Version Control & Immutability**: Semantic major/minor versioning with SHA-256 integrity verification. PostgreSQL immutability triggers block direct modification or deletion of approved versions and audit logs.
* **Baselines**: Faculty-locked snapshots capturing exact CI versions for formal milestones.
* **Change Control**: Multi-state Change Request (CR) lifecycle (`draft` -> `submitted` -> `under_review` -> `approved`/`rejected` -> `implemented` -> `verified` -> `closed`). Automated dependency impact analysis and unified side-by-side text diffing.
* **Status Accounting & Auditing**: Automatic immutable audit logging for every lifecycle event and state transition.
* **Releases**: Milestone-tagged release candidate packaging tied to baselines with verification of tests and documentation approvals.
* **Evaluation System**: Total marks allocation with flexible criteria validation and automatic percentage-to-letter grade conversion.
* **GitHub Integration**: Links teams to external GitHub repositories, tracks commits and branches, and enforces GitFlow/branching policies without attempting to replace Git.

---

## 2. Tech Stack

* **Frontend**: React + TypeScript (strict) + Vite + React Router v7 + TanStack Query. Handcrafted plain CSS UI (#f4f4f0 canvas, #2b5c84 accent, uppercase bordered badges, no icon libraries, no emoji). OpenAPI typed contract via `openapi-typescript`.
* **Backend**: Python 3.13 + FastAPI + SQLAlchemy 2.x + Alembic + Pydantic v2 + argon2-cffi + PyJWT + APScheduler + httpx + pytest.
* **Database**: PostgreSQL 16 with CHECK constraints, foreign keys, and custom PostgreSQL database triggers.
* **DevOps**: Docker, `docker-compose.yml`, and GitHub Actions CI workflow.

---

## 3. Implemented Feature Checklist

- [x] **Identity & Access Management**
  - [x] Student registration with unique Register Number (`23MIS0475`, etc.).
  - [x] Faculty registration with Faculty Code (`FAC0101`, etc.).
  - [x] Dual-identifier login (Email or Student Register Number / Faculty Code).
  - [x] Argon2 password hashing and JWT authentication.
  - [x] Account lockout mechanism after 5 consecutive failed attempts.
- [x] **Course & Project Management**
  - [x] Faculty course creation (`CSE3001`, etc.).
  - [x] Project configuration with custom policies (team sizes, hybrid/student/faculty formation modes, allowed extensions, late submission penalties, Git requirements).
  - [x] Themes, outcomes, CI templates, deadlines, and evaluation criteria setup.
  - [x] Bulk student enrollment via comma/newline separated register numbers with enrollment limit enforcement.
- [x] **Teams & Proposals**
  - [x] Student and faculty team formation workflows.
  - [x] Student team invitation system with real-time accept/reject.
  - [x] Multi-revision proposal submission, faculty review, revision requests, and approval.
  - [x] Automatic team lifecycle state transitions.
- [x] **SCM Core Engine**
  - [x] Configuration Item (CI) creation with automatic CI code sequence generation.
  - [x] Semantic version bumping (major/minor) and file uploading with SHA-256 deduplication.
  - [x] Cyclic dependency detection algorithm for CI graph.
  - [x] Milestone Baseline locking (locks all included CIs against direct edits).
  - [x] Direct CI edit prevention when locked in a baseline.
- [x] **Change Control (CR Engine)**
  - [x] Formal Change Request submission linked to locked baseline items.
  - [x] Automatic dependency impact analysis graph generator.
  - [x] Change Control Board (Faculty) review and approval/rejection workflow.
  - [x] Implemented version replacement and verification workflow.
  - [x] Side-by-side / unified text diff viewer for artifact versions.
- [x] **GitHub & Progress Tracking**
  - [x] Repository linking and branch policy validation (`gitflow_lite`).
  - [x] Commit logging and Git commit SHA enforcement for releases.
  - [x] Weekly progress reports with blocker tracking and screenshot uploads.
  - [x] Milestone file submission with late-flagging and automated penalty deduction.
- [x] **Releases & Evaluation**
  - [x] Release candidate requests tied to locked baselines.
  - [x] Release verification gates (tests passed, documentation approved, all baseline CIs approved).
  - [x] Evaluation marking by criteria with aggregate percentage and letter grade mapping (`S`, `A`, `B`, `C`, `D`, `F`).
- [x] **Audit & Notifications**
  - [x] PostgreSQL immutable trigger-backed audit logs.
  - [x] In-app real-time notification alerts with unread counter.
  - [x] Scheduled background reminders for upcoming deadlines.

---

## 4. Default Seed Accounts

The database seed (`backend/seed.py`) provisions a sample university setup:

| Role | Name | Identifier / Email | Password |
| :--- | :--- | :--- | :--- |
| **Faculty** | Dr. K. Meenakshi | `FAC-CSE-001` / `meenakshi.k@univ.edu` | `Password123!` |
| **Student** | Aarav Sharma (Leader) | `23MIS0475` / `aarav.s@univ.edu` | `Password123!` |
| **Student** | Diya Patel | `23MIS0476` / `diya.p@univ.edu` | `Password123!` |
| **Student** | Rohan Verma | `23MIS0477` / `rohan.v@univ.edu` | `Password123!` |
| **Student** | Ananya Iyer (Leader) | `23MIS0480` / `ananya.i@univ.edu` | `Password123!` |
| **Student** | Vikram Sundaram | `23MIS0481` / `vikram.s@univ.edu` | `Password123!` |
| **Student** | Sneha Reddy | `23MIS0482` / `sneha.r@univ.edu` | `Password123!` |
| **Student** | Karthik Nair (Leader) | `23MIS0490` / `karthik.n@univ.edu` | `Password123!` |
| **Student** | Pooja Menon | `23MIS0491` / `pooja.m@univ.edu` | `Password123!` |
| **Student** | Rahul Joshi | `23MIS0492` / `rahul.j@univ.edu` | `Password123!` |
| **Student** | Tanvi Kulkarni | `23MIS0501` / `tanvi.k@univ.edu` | `Password123!` |
| **Student** | Aditya Rao | `23MIS0502` / `aditya.r@univ.edu` | `Password123!` |
| **Student** | Meera Deshmukh | `23MIS0503` / `meera.d@univ.edu` | `Password123!` |

---

## 5. Local Setup & Running

### Prerequisites
* Python 3.12 or 3.13
* Node.js 20+ & npm
* PostgreSQL 16 running on localhost:5432 with databases `cpcms` and `cpcms_test` (or Docker)

### Backend Setup
```bash
cd backend
python -m venv .venv
# On Windows:
.venv\Scripts\activate
# On Linux/macOS:
source .venv/bin/activate

pip install -r requirements.txt
alembic upgrade head
python seed.py
uvicorn app.main:app --reload --port 8000
```

### Frontend Setup
```bash
cd frontend
npm install
npm run dev
```
Frontend runs at `http://localhost:5173`.

### Docker Compose
To run all services with one command:
```bash
docker-compose up --build
```

---

## 6. Running Tests

### Backend Pytest Suite
```bash
cd backend
python -m pytest -v
```
*(Executes all 16 test cases covering auth, locking, immutability triggers, CR impact analysis, evaluations, and releases).*

### Frontend Vitest Suite
```bash
cd frontend
npm test
```

### Frontend Typecheck & Production Build
```bash
cd frontend
npm run build
```

---

## 7. Architectural Assumptions

1. **SCM Immutability**: PostgreSQL triggers enforce append-only security for `ci_versions` and `audit_logs`. Mutable metadata (such as review status) is isolated while content digests and file references are strictly protected.
2. **Student ID Identity**: Register numbers are normalized to uppercase (e.g. `23MIS0475`) and act as first-class login credentials alongside university email addresses.
3. **Change Request Isolation**: Modifying a baseline-locked CI is prohibited unless authorized through an approved Change Request (CR), ensuring traceability.
4. **University Tool Design Principles**: The user interface follows standard institutional ergonomics—high data density, accessible forms, bordered state indicators, native controls, and clear typography without unnecessary decorative elements.
