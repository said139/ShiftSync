# ShiftSync — REST API Reference Documentation

Interactive OpenAPI / Swagger documentation is served automatically by `drf-spectacular`:
- **Swagger UI**: `http://127.0.0.1:8000/api/docs/`
- **ReDoc**: `http://127.0.0.1:8000/api/redoc/`
- **OpenAPI 3.0 Schema**: `http://127.0.0.1:8000/api/schema/`

---

## 1. Authentication & Account Security (`/api/auth/`)

| Method | Endpoint | Permission | Description |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/auth/login/` | Public (Rate-limited) | Authenticates `email` and `password`. Returns short-lived JWT `access` token (kept in browser memory), user profile, and sets `HttpOnly` refresh cookie (`shiftsync_refresh_token`). |
| `POST` | `/api/auth/refresh/` | Public (Cookie / Token) | Rotates refresh token from `HttpOnly` cookie or request body and issues a fresh `access` token. |
| `POST` | `/api/auth/logout/` | Public / Authenticated | Blacklists refresh token and clears `HttpOnly` cookie. |
| `GET`, `PATCH` | `/api/auth/me/` | Authenticated | Retrieves or updates current user profile settings. |
| `POST` | `/api/auth/change-password/` | Authenticated | Validates current password and sets a new password. |
| `POST` | `/api/auth/password-recovery/` | Public | Generates a time-limited password reset token. |
| `POST` | `/api/auth/password-reset/` | Public | Validates reset token and updates password. |

---

## 2. Users, Roles & Organisation Config (`/api/users/`, `/api/organisations/`)

| Method | Endpoint | Permission | Description |
| :--- | :--- | :--- | :--- |
| `GET`, `POST` | `/api/users/` | Admin (`GET` also Supervisor) | Lists organisation users or provisions a new user account with role and department. |
| `GET`, `PATCH` | `/api/users/:id/` | Admin | Retrieves or updates a user's role, department, or credentials. |
| `POST` | `/api/users/:id/toggle-status/` | Admin | Activates or deactivates a user account. |
| `GET` | `/api/users/colleagues/` | Authenticated | Lists active colleagues in the caller's organisation for shift/handover selection. |
| `GET`, `PATCH` | `/api/organisations/current/` | `GET`: All; `PATCH`: Admin | Reads or updates organisation task categories, departments, and NLP thresholds. |
| `GET` | `/api/organisations/audit-logs/` | Supervisor / Admin | Lists immutable system and handover audit events. |

---

## 3. Shifts, Handover Reports, Tasks & Acknowledgment (`/api/`)

| Method | Endpoint | Permission | Description |
| :--- | :--- | :--- | :--- |
| `GET`, `POST` | `/api/shifts/` | `GET`: All; `POST`: Admin | Lists shifts (filterable by `my_shifts`, `status`, `shift_date`) or creates/assigns a shift. |
| `GET`, `POST` | `/api/handovers/` | `GET`: All; `POST`: Outgoing/Admin | Lists handover reports (with role/org isolation) or creates a new `DRAFT` report. |
| `GET`, `PATCH`, `DELETE` | `/api/handovers/:id/` | Authenticated (Draft owner/Admin for `PATCH`/`DELETE`) | Inspects handover details or updates a saved `DRAFT`. Locked once `SUBMITTED`. |
| `POST` | `/api/handovers/:id/submit/` | Submitting Outgoing Worker / Admin | Atomically transitions a `DRAFT` handover to `SUBMITTED`, records `submitted_at`, prevents duplicates, and notifies incoming worker & supervisors. |
| `POST` | `/api/handovers/:id/acknowledge/` | Designated Incoming Worker / Admin | Explicitly acknowledges a `SUBMITTED` handover, records `acknowledged_by` & `acknowledged_at`, creates `AcknowledgmentEvent`, and carries forward unfinished tasks. |
| `POST` | `/api/handovers/:id/amend/` | Submitting Worker / Supervisor / Admin | Appends an immutable `HandoverAmendment` to a submitted/acknowledged report. |
| `GET`, `POST` | `/api/tasks/` | Authenticated | Lists or creates shift tasks with NLP suggestions and worker-confirmed overrides. |
| `POST` | `/api/tasks/:id/update-status/` | Authenticated | Updates task status (`Pending`, `In Progress`, `Completed`) and appends `TaskStatusHistory`. |
| `GET` | `/api/acknowledgments/` | Authenticated | Lists formal acknowledgment events (`mine_only=true` supported). |

---

## 4. NLP Service, Dashboards & Notifications (`/api/nlp/`, `/api/analytics/`, `/api/notifications/`)

| Method | Endpoint | Permission | Description |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/nlp/predict/` | Authenticated | Preprocesses task description and runs the fine-tuned Hugging Face Transformer classifier (or fallback), returning `category`, `priority`, `confidence_score`, and `is_low_confidence`. |
| `POST` | `/api/nlp/analyze-log/` | Authenticated | Segments a multi-task shift log narrative and classifies each discrete task. |
| `GET` | `/api/nlp/status/` | Authenticated | Returns active NLP provider status and test evaluation metrics. |
| `GET` | `/api/analytics/dashboard/` | Authenticated | Calculates live dashboard metric cards, completion trend chart, critical issues, and recent handovers from PostgreSQL. |
| `GET` | `/api/analytics/supervisor-report/` | Supervisor / Admin | Returns filtered supervisory analytics, NLP override rates, and category/priority breakdowns. |
| `GET` | `/api/analytics/export-csv/` | Supervisor / Admin | Exports filtered handover performance records as a CSV download. |
| `GET` | `/api/notifications/` | Authenticated | Lists persistent in-app notifications (`unread-count/`, `:id/mark-read/`, `mark-all-read/`). |
