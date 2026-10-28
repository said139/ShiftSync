# ShiftSync — Role-Based User Guide

ShiftSync formalises operational handovers across four strictly separated user roles.

---

## 1. Outgoing Worker Guide

**Demo Account**: `outgoing@shiftsync.ac.ke` / `ShiftSync@2026!`

1. **View Assigned Shifts**: Open **Shift Management** (`/shifts`) to inspect your active shift, shift window, and scheduled incoming counterpart.
2. **Prepare Handover Report**: Click **Create Handover Report** (`/handovers/create`):
   - **Step 1**: Select your active shift and verify the designated incoming worker.
   - **Step 2 & 3 (NLP Assist)**: Enter a task description in natural language and click **Suggest Category & Priority (NLP)** (or tab out of the field). The fine-tuned Hugging Face Transformer suggests a category, priority (`Low`, `Medium`, `High`, `Critical`), status, and confidence score.
   - **Manual Override**: Review the NLP suggestion and accept or manually override the category or priority before clicking **Add Task to Handover Report**. Both the model's prediction and your confirmed values are preserved.
   - **Equipment & Safety**: Select the overall equipment status and record any safety issues or near misses.
   - **Step 4 (Save Draft)**: Click **Save Draft** at any time to persist your draft in PostgreSQL. Refreshing the browser will not lose your work.
   - **Step 5 (Submit Formally)**: Click **Review & Submit Handover**, verify the summary card, and click **Confirm & Formally Submit Handover**. Once submitted, the report is locked and the incoming worker is notified.

---

## 2. Incoming Worker Guide

**Demo Account**: `incoming@shiftsync.ac.ke` / `ShiftSync@2026!`

1. **Review Assigned Handovers**: Open **Incoming Review & Ack** (`/handovers/incoming`) or click the notification alert in the top bar.
2. **Inspect Tasks & Safety Notes**: Review all recorded tasks, critical priorities, equipment statuses, and safety observations. Merely opening or viewing a handover report never marks it acknowledged.
3. **Explicit Acknowledgment**: Enter your incoming sign-off notes, check the verification confirmation box, and click **Formally Acknowledge Handover Receipt**.
4. **Carried-Forward Tasks**: Upon acknowledgment, your identity and UTC timestamp are recorded, the outgoing worker is notified, and any unfinished tasks (`Pending` or `In Progress`) are carried forward into **Task Tracking** (`/tasks`) for completion during your shift.

---

## 3. Supervisor Guide

**Demo Account**: `supervisor@shiftsync.ac.ke` / `ShiftSync@2026!`

1. **Supervisor Dashboard**: Open **Supervisor Dashboard** (`/supervisor/dashboard`) to monitor organisation-wide active shifts, handovers awaiting acknowledgment, unresolved tasks, critical-priority items, and handover completion rates over time.
2. **Handover Analytics & CSV Export**: Open **Handover Analytics & Reports** (`/supervisor/analytics`) to filter handovers by date range, shift, status, worker, and priority, inspect NLP acceptance vs override statistics, and click **Export CSV Performance Report**.
3. **Historical Audit**: Inspect any historical handover report (`/supervisor/history/:id`) or task audit trail (`/tasks`).

---

## 4. System Administrator Guide

**Demo Account**: `admin@shiftsync.ac.ke` / `ShiftSync@2026!`

1. **User Provisioning**: Open **User Management** (`/admin/users`) and **Create User Account** (`/admin/users/new`) to create accounts, assign roles (`OUTGOING_WORKER`, `INCOMING_WORKER`, `SUPERVISOR`, `ADMIN`), assign departments, and activate/deactivate accounts.
2. **Shift Creation & Assignment**: Open **Create & Assign Shift** (`/admin/shifts/new`) to schedule shifts and assign outgoing/incoming worker pairs.
3. **System Configuration & Audit Logs**: Open **System Configuration** (`/admin/configuration`) to update configurable task categories, departments, NLP confidence thresholds, and inspect the immutable system-level `AuditEvent` log.
