# GOOGLE ANTIGRAVITY MASTER PROMPT — SHIFTSYNC

## 1. PROJECT OVERVIEW

Act as a senior full-stack software engineer, system architect, NLP engineer, UI/UX designer, database engineer, and QA tester.

Build **ShiftSync: A Shift Handover Management System with NLP for Automated Task Categorisation and Priority Detection**, a complete, functional, responsive web application designed for small and medium-sized shift-based organisations.

The application addresses the problems associated with informal shift handovers, including missed tasks, incomplete information transfer, unclear responsibility, duplicated work, and poor supervisory oversight.

The system must formalise the transfer of responsibilities between outgoing and incoming workers through structured task records, mandatory handover acknowledgment, persistent audit trails, and a supervisor dashboard.

This is an academic Informatics and Computer Science project. The implementation must be technically sound, demonstrable, maintainable, and aligned with the approved project proposal.

**Build a real full-stack application, not a static mockup.** Implement the frontend, backend, database, NLP functionality, authentication, role permissions, and testing.

## 2. MANDATORY TECHNOLOGY STACK

Use the following technologies as specified in the project proposal.

Frontend:
- React.js
- JavaScript or TypeScript, using a consistent approach throughout the project
- React Router for navigation
- Axios for communicating with the backend REST API
- A consistent, reusable component system and responsive styling

Backend:
- Python
- Django
- Django REST Framework
- Django REST Framework Simple JWT for authentication
- Django ORM for database operations

Database:
- PostgreSQL
- Proper relational database design, migrations, foreign keys, indexes, and constraints

NLP:
- Hugging Face Transformers
- A pre-trained transformer-based text classification model, fine-tuned if an appropriate labelled dataset is available
- Python-based preprocessing and inference integrated with Django

Testing and deployment:
- pytest and Django REST Framework API tests for the backend
- Jest and React Testing Library for frontend tests
- Playwright for end-to-end testing
- GitHub Actions for continuous integration
- Nginx and Gunicorn for production deployment on Ubuntu

Do not replace the required stack with Firebase, Supabase, Next.js, Node.js, or another alternative stack.

Inspect the existing workspace first. Preserve useful existing code and configuration rather than rebuilding the project unnecessarily.

## 3. USER ROLES AND PERMISSIONS

Implement four clearly separated user roles.

### A. Outgoing Worker

The outgoing worker must be able to:
- Log in securely.
- View their assigned and current shift information.
- Record completed, pending, and in-progress tasks.
- Enter task descriptions using natural language.
- Receive suggested task categories and priority levels from the NLP component.
- Review and manually correct NLP suggestions before saving.
- Add contextual notes, equipment status, safety issues, and near misses.
- Create a handover report as a draft.
- Edit a draft before submission.
- Designate the appropriate incoming worker.
- Submit the handover formally.
- View the submitted handover and its acknowledgment status.
- View historical handovers they are authorised to access.

### B. Incoming Worker

The incoming worker must be able to:
- Log in securely.
- View handovers assigned to them.
- Review the outgoing worker's handover report.
- Inspect individual tasks, task priorities, equipment status, safety issues, and contextual notes.
- Identify unresolved and critical tasks.
- Formally acknowledge receipt of the handover.
- Have their identity and acknowledgment timestamp recorded.
- View the tasks carried forward into their shift.
- View their acknowledgment history.

A handover must not be marked acknowledged merely because an incoming worker opens or views it.

The acknowledgment must result from an explicit user action.

### C. Supervisor

The supervisor must be able to:
- View an organisation-wide dashboard for their authorised organisational scope.
- Monitor active shifts and scheduled shifts.
- View submitted, pending, and acknowledged handovers.
- Identify incomplete tasks and critical-priority items.
- Monitor unresolved tasks carried forward between shifts.
- View handover completion and acknowledgment rates over a selected date range.
- Access historical handover reports and acknowledgment timestamps.
- Filter records by date, shift, status, worker, and priority where applicable.
- Inspect individual task records and their history.
- Generate and export basic handover performance reports.
- Monitor in-app notifications concerning relevant handover events.

Supervisors must have read access to operational records within their authorised scope. Do not automatically grant them administrative privileges.

### D. System Administrator

The administrator must be able to:
- Create and manage user accounts.
- Assign and update user roles.
- Assign users to departments or organisations.
- Activate or deactivate accounts.
- Create and manage shifts.
- Assign outgoing and incoming workers to shifts.
- View system-level records and relevant operational activity.
- Maintain the basic configuration required by the application.

Enforce all permissions on the Django backend. Hiding navigation items in React is not sufficient security.

## 4. REQUIRED APPLICATION PAGES

Build the following pages with consistent layouts, working navigation, and appropriate role-based access.

### Public and authentication pages
1. Login page.
2. Password recovery and reset flow.
3. Access-denied page.
4. Not-found page.

Account creation and provisioning must follow the intended administrative workflow rather than allowing unrestricted public registration.

### Shared application pages
5. Dashboard overview.
6. User profile and account settings.
7. Notifications centre.
8. Handover history.

### Operational pages
9. Shift management.
10. Create handover report.
11. Log shift activity.
12. Task tracking.
13. Handover report details.
14. Incoming handover review and acknowledgment.

### Supervisory pages
15. Supervisor dashboard.
16. Handover analytics and basic reports.
17. Historical handover details.

### Administrative pages
18. User management.
19. Create and edit user.
20. Create and edit shifts.
21. Basic system configuration.

Use a shared sidebar or navigation system appropriate to the user's role. On mobile, the navigation must adapt to a compact menu.

Do not create disconnected pages simply to satisfy this list. Every page must connect to real application workflows.

## 5. DASHBOARD DESIGN

Create a professional operational dashboard that communicates the state of the organisation's shifts immediately.

Include metric cards for:
- Active shifts.
- Handovers awaiting acknowledgment.
- Submitted handovers.
- Unresolved tasks.
- Critical-priority tasks.
- Handover completion rate.

Below the metric cards, display:
- Recent handover reports.
- Outstanding tasks.
- Critical issues requiring attention.
- Upcoming or active shifts.
- Recent system notifications.
- A chart showing handover completion rates over time.

The dashboard must retrieve its data from Django REST API endpoints backed by PostgreSQL.

All metrics must be calculated from actual stored records, using clearly defined denominators and date ranges. Do not hardcode dashboard numbers or generate misleading sample statistics.

Display different information to different roles. For example, workers should see their relevant operational information, while supervisors can see aggregated information for their authorised organisation.

Include date filters, loading states, empty states, and error handling.

## 6. TASK LOGGING AND HANDOVER WORKFLOW

This is the central workflow of ShiftSync. Implement it completely.

### Step 1: Select the shift

The outgoing worker selects the relevant shift. Display the shift date, start time, end time, assigned outgoing worker, and designated incoming worker.

Populate the authenticated worker's identity automatically wherever appropriate.

Validate that the selected shift and worker assignments are valid.

### Step 2: Record shift activity

Provide a structured interface containing:
- Free-text task description.
- Task status.
- Suggested task category.
- Suggested priority.
- Optional contextual notes.
- Optional due date.
- Equipment status.
- Safety issues and near misses.

Allow multiple tasks to be recorded in one handover.

### Step 3: Run NLP categorisation and priority detection

When a worker enters a task description, send the text to a Django API endpoint that invokes the NLP component.

The system should suggest:
- A task category.
- A priority level: Low, Medium, High, or Critical.
- A confidence score where supported by the model.

Use the categories appropriate to the target shift-based environment, such as maintenance, safety, equipment, operations, inventory, customer service, and other.

Treat these as initial configurable categories rather than an exhaustive industry taxonomy.

The worker must be able to accept or override the model's suggestions before saving the task.

Preserve the original description and the final user-confirmed category and priority. Do not silently overwrite the worker's decisions with subsequent model predictions.

### Step 4: Save a draft

Allow the outgoing worker to save the report without submitting it.

Drafts must be persisted in PostgreSQL and remain editable by the authorised outgoing worker.

A page refresh must not erase a saved draft.

### Step 5: Submit the handover

Before submission, display a review screen showing all recorded tasks, their statuses, priorities, notes, equipment status, and safety issues.

Validate the required fields and the selected shift assignment.

On submission:
- Save the report and its tasks in a database transaction.
- Record the submission timestamp.
- Record the submitting user.
- Change the handover status from Draft to Submitted.
- Make the report available to the designated incoming worker.
- Create an in-app notification for the relevant recipient.
- Prevent accidental duplicate submissions.
- Prevent ordinary editing of a submitted report.

If a correction mechanism is required, implement it through an explicitly authorised, auditable amendment process rather than silently rewriting submitted records.

### Step 6: Incoming acknowledgment

The designated incoming worker opens the submitted handover and reviews its contents.

Provide a clear acknowledgment action after the report has been displayed for review.

On acknowledgment:
- Record the acknowledging user's identity.
- Record the acknowledgment timestamp.
- Update the handover status to Acknowledged.
- Notify the outgoing worker through the in-app notification system.
- Update the supervisor dashboard.
- Preserve the acknowledgment event in the audit history.

Only the designated incoming worker, or another explicitly authorised user under a defined workflow, may acknowledge the report.

### Step 7: Track outstanding work

Tasks that remain pending or in progress must be visible to the incoming shift and authorised supervisors.

Preserve task history and responsibility when work is carried forward. Do not automatically mark unfinished tasks as completed when a handover is acknowledged.

Distinguish the status of a handover report from the status of its individual tasks.

## 7. NLP IMPLEMENTATION REQUIREMENTS

The NLP feature is a core academic objective of ShiftSync, not a decorative feature.

Build a dedicated, modular NLP service that can classify task descriptions and predict task priority.

### Required architecture

1. Receive the task description from the frontend.
2. Validate and preprocess the text.
3. Run inference using the configured classification model.
4. Return the predicted category, priority, and supported confidence information.
5. Display the predictions to the worker.
6. Allow the worker to accept or correct the suggestions.
7. Persist both the model suggestions and the worker-confirmed values where appropriate.

### Model and dataset

Use Hugging Face Transformers for model loading, inference, and fine-tuning.

Inspect the available project files for a labelled dataset before deciding on the training approach.

If an appropriate dataset is available:
- Inspect its labels and quality.
- Split the data into training, validation, and test sets without leakage.
- Fine-tune an appropriate pre-trained transformer model.
- Save the model and tokenizer in a reproducible manner.
- Evaluate performance using precision, recall, and F1-score.
- Report per-class performance where possible.

If no suitable labelled dataset is available:
- Do not fabricate a trained model or claim that fine-tuning has occurred.
- Build the NLP service interface and inference integration.
- Use an explicitly identified baseline classifier or a configurable pre-trained model if suitable.
- Document the dataset and training requirements for a properly fine-tuned model.
- Make the inference provider replaceable without redesigning the application.
- Clearly distinguish demonstrated NLP inference from a model that has actually been trained and evaluated on shift-handover data.

Support low-confidence predictions appropriately. Let workers make the final decision.

Do not send operational task descriptions to external AI services unless the project is explicitly configured and authorised to do so.

The application must remain usable if the NLP model is unavailable. Display a clear message and allow manual task categorisation and prioritisation.

## 8. DATABASE DESIGN

Use PostgreSQL with Django models and migrations.

Implement at least the following core entities:
- Users (Custom user model with unique ID, full name, email, role, organisation/department, account status, timestamps)
- Shifts (Shift date, start/end times, outgoing worker, incoming worker, supervisor, shift status, organisation/department)
- Handover Reports (Associated shift, submitting worker, designated incoming worker, equipment status, safety issues/near misses, additional notes, report status: Draft/Submitted/Acknowledged, creation/submission/acknowledgment timestamps)
- Tasks (Associated handover/shift, description, category, status: Pending/In Progress/Completed, priority: Low/Medium/High/Critical, model-suggested category & priority, worker-confirmed category & priority, confidence score, assignee, due date, contextual notes, timestamps)
- Notifications (Recipient, type, related handover/task, message, read/unread status, creation timestamp)
- Supporting entities: Acknowledgment events, task status history, and audit events.

## 9. AUTHENTICATION AND SECURITY

Implement secure JWT authentication using Django REST Framework Simple JWT:
- POST /api/auth/login/
- POST /api/auth/refresh/
- Password recovery and reset endpoints.
- Keep access tokens in browser memory. Avoid storing authentication tokens in localStorage.
- Backend-enforced RBAC, organisation-level data isolation, password validation, rate limiting, CORS, input validation, safe error responses, CSRF protections, audit logging, and environment-based secrets.

## 10. REST API REQUIREMENTS

Documented, consistent REST endpoints for Authentication, Users & roles, Shifts, Handover reports, Task logging & updates, NLP predictions, Handover acknowledgment, Notifications, Supervisor dashboard metrics, and Historical records & reports. OpenAPI documentation compatible with DRF.

## 11. USER INTERFACE AND VISUAL DESIGN

Professional operational management application:
- Clean, modern, structured dashboard with professional navy, slate, and restrained teal accents.
- Status badges using colour alongside text/icons (Green = completed/success, Amber = pending/high-attention, Red = critical/errors).
- Responsive layouts for phones, tablets, and desktop computers.

## 12. NOTIFICATIONS AND SCOPE CONTROL

Persistent in-app notifications with unread counts and mark-as-read via API polling/refresh.

## 13. TESTING REQUIREMENTS

- Backend tests: pytest and DRF API tests.
- NLP tests: representative descriptions, malformed inputs, low-confidence, unavailable models, manual override handling.
- Frontend tests: Jest and React Testing Library.
- End-to-end tests: Playwright covering the 14-step complete workflow and negative/security cases.

## 14. PROJECT STRUCTURE AND DOCUMENTATION

Maintain separate `frontend/` and `backend/` applications, an isolated NLP module, `.env.example`, database migrations, seed command, test suites, API docs, schema docs, Ubuntu/Nginx/Gunicorn deployment guide, GitHub Actions CI, and User Guide.
