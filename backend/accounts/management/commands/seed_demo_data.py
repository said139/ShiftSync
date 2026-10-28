from datetime import date, time, timedelta
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from accounts.models import AuditEvent, Organisation, User, UserRole
from notifications.models import Notification, NotificationType
from operations.models import (
    AcknowledgmentEvent,
    EquipmentStatusChoice,
    HandoverReport,
    HandoverStatus,
    Shift,
    ShiftStatus,
    Task,
    TaskPriority,
    TaskStatus,
    TaskStatusHistory,
)

DEFAULT_PASSWORD = "ShiftSync@2026!"


class Command(BaseCommand):
    help = (
        "Seeds realistic ShiftSync demonstration data across all 4 roles "
        "(Outgoing Worker, Incoming Worker, Supervisor, System Administrator) "
        "and a second organisation for multi-tenant isolation testing."
    )

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write("Seeding ShiftSync demonstration environment...")

        # 1. Primary Organisation
        org_kq, _ = Organisation.objects.update_or_create(
            code="KQ-MRO",
            defaults={
                "name": "Kenya Airways Line Maintenance & Flight Ops (JKIA)",
                "industry": "Aviation Maintenance & Shift Operations",
                "departments": [
                    "Line Maintenance",
                    "Avionics & Flight Control Systems",
                    "Flight Operations",
                    "Safety & Quality Assurance",
                    "Logistics & Stores",
                ],
                "task_categories": [
                    "Maintenance",
                    "Safety & Compliance",
                    "Equipment Check",
                    "Operations",
                    "Inventory",
                    "Customer Service",
                    "Administration",
                    "Other",
                ],
                "priority_levels": ["Low", "Medium", "High", "Critical"],
                "require_acknowledgment_notes": False,
                "low_confidence_threshold": 60.0,
                "nlp_enabled": True,
            },
        )

        # 2. Secondary Organisation (for cross-organisation isolation tests)
        org_port, _ = Organisation.objects.update_or_create(
            code="MPA-OPS",
            defaults={
                "name": "Mombasa Terminal Logistics Operations",
                "industry": "Maritime & Terminal Operations",
                "departments": ["Crane Operations", "Yard Safety"],
            },
        )

        # 3. Create Role-Specific Users in Primary Organisation
        users_spec = [
            (
                "said@kq.ac.ke",
                "Eng. Said Marika",
                "KQ-ENG-001",
                UserRole.ADMIN,
                "IT & Systems Governance",
                True,
            ),
            (
                "david@kq.ac.ke",
                "Eng. David Ochieng",
                "KQ-ENG-002",
                UserRole.OUTGOING_WORKER,
                "Line Maintenance",
                False,
            ),
            (
                "amina@kq.ac.ke",
                "Eng. Amina Hassan",
                "KQ-ENG-003",
                UserRole.INCOMING_WORKER,
                "Line Maintenance",
                False,
            ),
            (
                "grace@kq.ac.ke",
                "Capt. Grace Wanjiku",
                "KQ-OPS-001",
                UserRole.SUPERVISOR,
                "Safety & Quality Assurance",
                False,
            ),
            (
                "admin@shiftsync.ac.ke",
                "Eng. Said Marika (SysAdmin)",
                "EMP-ADM-001",
                UserRole.ADMIN,
                "IT & Systems Governance",
                True,
            ),
            (
                "supervisor@shiftsync.ac.ke",
                "Capt. Grace Wanjiku (Supervisor)",
                "EMP-SUP-102",
                UserRole.SUPERVISOR,
                "Safety & Quality Assurance",
                False,
            ),
            (
                "outgoing@shiftsync.ac.ke",
                "Eng. David Ochieng (Outgoing)",
                "EMP-OUT-201",
                UserRole.OUTGOING_WORKER,
                "Line Maintenance",
                False,
            ),
            (
                "incoming@shiftsync.ac.ke",
                "Eng. Amina Hassan (Incoming)",
                "EMP-INC-202",
                UserRole.INCOMING_WORKER,
                "Line Maintenance",
                False,
            ),
            (
                "outgoing2@shiftsync.ac.ke",
                "Tech. Kevin Kiprop (Outgoing B)",
                "EMP-OUT-203",
                UserRole.OUTGOING_WORKER,
                "Avionics & Flight Control Systems",
                False,
            ),
            (
                "incoming2@shiftsync.ac.ke",
                "Tech. Faith Njoroge (Incoming B)",
                "EMP-INC-204",
                UserRole.INCOMING_WORKER,
                "Avionics & Flight Control Systems",
                False,
            ),
        ]

        created_users = {}
        for email, full_name, emp_id, role, dept, is_staff in users_spec:
            u, _ = User.objects.update_or_create(
                email=email,
                defaults={
                    "full_name": full_name,
                    "employee_id": emp_id,
                    "role": role,
                    "organisation": org_kq,
                    "department": dept,
                    "phone_number": "+254 700 123456",
                    "is_active": True,
                    "is_staff": is_staff,
                    "is_superuser": is_staff,
                },
            )
            u.set_password(DEFAULT_PASSWORD)
            u.save(update_fields=["password"])
            created_users[email] = u

        ext_user, _ = User.objects.update_or_create(
            email="external@mombasaport.co.ke",
            defaults={
                "full_name": "Hassan Bakari (External Org)",
                "employee_id": "MPA-009",
                "role": UserRole.INCOMING_WORKER,
                "organisation": org_port,
                "department": "Crane Operations",
                "is_active": True,
            },
        )
        ext_user.set_password(DEFAULT_PASSWORD)
        ext_user.save(update_fields=["password"])

        admin_u = created_users["admin@shiftsync.ac.ke"]
        sup_u = created_users["supervisor@shiftsync.ac.ke"]
        out_u = created_users["outgoing@shiftsync.ac.ke"]
        inc_u = created_users["incoming@shiftsync.ac.ke"]
        out2_u = created_users["outgoing2@shiftsync.ac.ke"]
        inc2_u = created_users["incoming2@shiftsync.ac.ke"]

        said_kq = created_users["said@kq.ac.ke"]
        david_kq = created_users["david@kq.ac.ke"]
        amina_kq = created_users["amina@kq.ac.ke"]
        grace_kq = created_users["grace@kq.ac.ke"]

        today = date.today()
        yesterday = today - timedelta(days=1)
        two_days_ago = today - timedelta(days=2)
        tomorrow = today + timedelta(days=1)

        # 4. Create Shifts
        shift_hist, _ = Shift.objects.update_or_create(
            organisation=org_kq,
            name="DEMO — Day Line Maintenance Alpha (Completed)",
            shift_date=two_days_ago,
            defaults={
                "department": "Line Maintenance",
                "start_time": time(6, 0),
                "end_time": time(14, 0),
                "outgoing_worker": out_u,
                "incoming_worker": inc_u,
                "supervisor": sup_u,
                "status": ShiftStatus.COMPLETED,
                "notes": "[DEMO DATA] Historical completed shift with acknowledged handover.",
            },
        )

        shift_yesterday, _ = Shift.objects.update_or_create(
            organisation=org_kq,
            name="DEMO — Night Turnaround & Avionics Bravo",
            shift_date=yesterday,
            defaults={
                "department": "Avionics & Flight Control Systems",
                "start_time": time(14, 0),
                "end_time": time(22, 0),
                "outgoing_worker": out2_u,
                "incoming_worker": inc2_u,
                "supervisor": sup_u,
                "status": ShiftStatus.COMPLETED,
                "notes": "[DEMO DATA] Historical shift with acknowledged handover.",
            },
        )

        shift_active_awaiting, _ = Shift.objects.update_or_create(
            organisation=org_kq,
            name="DEMO — Morning Flight Ops & Line Maint A (Active)",
            shift_date=today,
            defaults={
                "department": "Line Maintenance",
                "start_time": time(6, 0),
                "end_time": time(14, 0),
                "outgoing_worker": out_u,
                "incoming_worker": inc_u,
                "supervisor": sup_u,
                "status": ShiftStatus.ACTIVE,
                "notes": "[DEMO DATA] Active shift with submitted handover awaiting incoming acknowledgment.",
            },
        )

        shift_active_draft, _ = Shift.objects.update_or_create(
            organisation=org_kq,
            name="DEMO — Afternoon Hangar Inspection Shift C (Active)",
            shift_date=today,
            defaults={
                "department": "Line Maintenance",
                "start_time": time(14, 0),
                "end_time": time(22, 0),
                "outgoing_worker": out_u,
                "incoming_worker": inc_u,
                "supervisor": sup_u,
                "status": ShiftStatus.ACTIVE,
                "notes": "[DEMO DATA] Active shift ready for outgoing worker task logging and draft handover.",
            },
        )

        shift_scheduled, _ = Shift.objects.update_or_create(
            organisation=org_kq,
            name="DEMO — Scheduled Morning Ramp Check Tomorrow",
            shift_date=tomorrow,
            defaults={
                "department": "Avionics & Flight Control Systems",
                "start_time": time(6, 0),
                "end_time": time(14, 0),
                "outgoing_worker": out2_u,
                "incoming_worker": inc2_u,
                "supervisor": sup_u,
                "status": ShiftStatus.SCHEDULED,
                "notes": "[DEMO DATA] Upcoming scheduled shift.",
            },
        )

        # Kenya Airways Personnel Shifts (said@kq.ac.ke, david@kq.ac.ke, amina@kq.ac.ke)
        shift_kq_line_maint, _ = Shift.objects.update_or_create(
            organisation=org_kq,
            name="KQ 787 Line Maintenance & Flight Ops (Bay 4)",
            shift_date=today,
            defaults={
                "department": "Line Maintenance",
                "start_time": time(6, 0),
                "end_time": time(14, 0),
                "outgoing_worker": david_kq,
                "incoming_worker": amina_kq,
                "supervisor": grace_kq,
                "status": ShiftStatus.ACTIVE,
                "notes": "[KQ OPERATIONS] Active Line Maintenance Shift. David is Outgoing, Amina is Incoming.",
            },
        )

        shift_kq_avionics, _ = Shift.objects.update_or_create(
            organisation=org_kq,
            name="KQ Fleet Avionics & Radar Calibration (Bay 2)",
            shift_date=today,
            defaults={
                "department": "Avionics & Flight Control Systems",
                "start_time": time(14, 0),
                "end_time": time(22, 0),
                "outgoing_worker": said_kq,
                "incoming_worker": david_kq,
                "supervisor": grace_kq,
                "status": ShiftStatus.ACTIVE,
                "notes": "[KQ OPERATIONS] Active Avionics Inspection. Said is Outgoing, David is Incoming.",
            },
        )

        # 5. Create Handover Reports & Tasks if not already seeded
        now = timezone.now()

        # Report 1: Historical Acknowledged Report (2 days ago)
        rep1, created1 = HandoverReport.objects.update_or_create(
            report_code="HND-DEMO-001",
            defaults={
                "organisation": org_kq,
                "shift": shift_hist,
                "submitting_worker": out_u,
                "designated_incoming_worker": inc_u,
                "acknowledged_by": inc_u,
                "equipment_status": EquipmentStatusChoice.OPERATIONAL,
                "equipment_details": "All hydraulic test rigs and ground power units operational.",
                "safety_issues": "None observed during shift.",
                "has_safety_incident": False,
                "additional_notes": "[DEMO RECORD] Completed routine transit checks on 5Y-KZA and 5Y-KZB.",
                "acknowledgment_notes": "Reviewed all transit logs and tool inventory. Confirmed receipt.",
                "status": HandoverStatus.ACKNOWLEDGED,
                "submitted_at": now - timedelta(days=2, hours=3),
                "acknowledged_at": now - timedelta(days=2, hours=2, minutes=42),
            },
        )
        if created1:
            t1 = Task.objects.create(
                organisation=org_kq,
                shift=shift_hist,
                handover_report=rep1,
                description="Checked Boeing 787 left engine oil and pressure sensor readings; parameter stable within flight envelope.",
                category="Equipment Check",
                confirmed_category="Equipment Check",
                model_suggested_category="Equipment Check",
                status=TaskStatus.COMPLETED,
                priority=TaskPriority.HIGH,
                confirmed_priority=TaskPriority.HIGH,
                model_suggested_priority=TaskPriority.HIGH,
                category_confidence=94.2,
                priority_confidence=91.5,
                confidence_score=92.9,
                nlp_provider_used="huggingface_transformer",
                created_by=out_u,
                assignee=inc_u,
                contextual_notes="Telemetry baseline verified.",
            )
            TaskStatusHistory.objects.create(
                task=t1,
                changed_by=out_u,
                previous_status="",
                new_status=TaskStatus.COMPLETED,
                previous_priority="",
                new_priority=TaskPriority.HIGH,
                comment="Completed during Morning Line Maint Alpha.",
            )
            AcknowledgmentEvent.objects.create(
                organisation=org_kq,
                handover_report=rep1,
                acknowledged_by=inc_u,
                acknowledgment_notes=rep1.acknowledgment_notes,
                unresolved_tasks_count=0,
                critical_tasks_count=0,
                ip_address="127.0.0.1",
            )

        # Report 2: Yesterday Acknowledged Report with a Carried-Forward Unresolved Task
        rep2, created2 = HandoverReport.objects.update_or_create(
            report_code="HND-DEMO-002",
            defaults={
                "organisation": org_kq,
                "shift": shift_yesterday,
                "submitting_worker": out2_u,
                "designated_incoming_worker": inc2_u,
                "acknowledged_by": inc2_u,
                "equipment_status": EquipmentStatusChoice.MINOR_ISSUE,
                "equipment_details": "Pitot-static test box #2 awaiting calibration sticker renewal.",
                "safety_issues": "Minor hydraulic fluid drip noticed near Bay 3 drip tray; absorbent pads placed.",
                "has_safety_incident": True,
                "additional_notes": "[DEMO RECORD] Handover acknowledged; cabin outflow valve calibration carried forward.",
                "acknowledgment_notes": "Acknowledged. Taking over the outflow valve calibration task on incoming shift.",
                "status": HandoverStatus.ACKNOWLEDGED,
                "submitted_at": now - timedelta(days=1, hours=2),
                "acknowledged_at": now - timedelta(days=1, hours=1, minutes=45),
            },
        )
        if created2:
            t2a = Task.objects.create(
                organisation=org_kq,
                shift=shift_yesterday,
                handover_report=rep2,
                description="Rectified cabin pressurization outflow valve hunting by cleaning valve throat and recalibrating stepper motor.",
                category="Maintenance",
                confirmed_category="Maintenance",
                model_suggested_category="Maintenance",
                status=TaskStatus.IN_PROGRESS,
                priority=TaskPriority.HIGH,
                confirmed_priority=TaskPriority.HIGH,
                model_suggested_priority=TaskPriority.HIGH,
                category_confidence=89.6,
                priority_confidence=88.1,
                confidence_score=88.9,
                nlp_provider_used="huggingface_transformer",
                created_by=out2_u,
                assignee=inc2_u,
                is_carried_forward=True,
                contextual_notes="Stepper motor recalibrated; awaiting 10-minute ground pressure decay test.",
            )
            TaskStatusHistory.objects.create(
                task=t2a,
                changed_by=inc2_u,
                previous_status=TaskStatus.IN_PROGRESS,
                new_status=TaskStatus.IN_PROGRESS,
                previous_priority=TaskPriority.HIGH,
                new_priority=TaskPriority.HIGH,
                comment="Carried forward into incoming shift upon formal acknowledgment of HND-DEMO-002.",
            )
            AcknowledgmentEvent.objects.create(
                organisation=org_kq,
                handover_report=rep2,
                acknowledged_by=inc2_u,
                acknowledgment_notes=rep2.acknowledgment_notes,
                unresolved_tasks_count=1,
                critical_tasks_count=0,
                ip_address="127.0.0.1",
            )

        # Report 3: Active Submitted Handover Awaiting Explicit Acknowledgment by Incoming Worker (`incoming@shiftsync.ac.ke`)
        rep3, created3 = HandoverReport.objects.update_or_create(
            report_code="HND-DEMO-003",
            defaults={
                "organisation": org_kq,
                "shift": shift_active_awaiting,
                "submitting_worker": out_u,
                "designated_incoming_worker": inc_u,
                "equipment_status": EquipmentStatusChoice.MAINTENANCE_REQUIRED,
                "equipment_details": "Hangar Bay 1 hydraulic mule pressure fluctuating above 3050 PSI; tagged for inspection.",
                "safety_issues": "Major safety alert: jet fuel seepage detected at engine pylon fuel disconnect coupling on 5Y-KZE; aircraft grounded pending seal swap.",
                "has_safety_incident": True,
                "additional_notes": "[DEMO RECORD] Urgent incoming review required for 5Y-KZE pylon fuel coupling seal replacement before evening dispatch.",
                "status": HandoverStatus.SUBMITTED,
                "submitted_at": now - timedelta(minutes=35),
            },
        )
        if created3:
            t3_crit = Task.objects.create(
                organisation=org_kq,
                shift=shift_active_awaiting,
                handover_report=rep3,
                description="Major safety alert: jet fuel seepage detected at engine pylon fuel disconnect coupling; aircraft grounded pending seal swap.",
                category="Safety & Compliance",
                confirmed_category="Safety & Compliance",
                model_suggested_category="Safety & Compliance",
                status=TaskStatus.PENDING,
                priority=TaskPriority.CRITICAL,
                confirmed_priority=TaskPriority.CRITICAL,
                model_suggested_priority=TaskPriority.CRITICAL,
                category_confidence=97.4,
                priority_confidence=96.8,
                confidence_score=97.1,
                nlp_provider_used="huggingface_transformer",
                created_by=out_u,
                assignee=inc_u,
                due_date=now + timedelta(hours=3),
                contextual_notes="Replacement fluorocarbon seal kit drawn from Bonded Store Bin #A-14.",
            )
            t3_prog = Task.objects.create(
                organisation=org_kq,
                shift=shift_active_awaiting,
                handover_report=rep3,
                description="Checked main landing gear brake wear indicator pins and hydraulic accumulator pre-charge at 3000 PSI nominal.",
                category="Equipment Check",
                confirmed_category="Equipment Check",
                model_suggested_category="Equipment Check",
                status=TaskStatus.IN_PROGRESS,
                priority=TaskPriority.HIGH,
                confirmed_priority=TaskPriority.HIGH,
                model_suggested_priority=TaskPriority.MEDIUM,
                was_overridden=True,
                category_confidence=91.0,
                priority_confidence=74.5,
                confidence_score=82.8,
                nlp_provider_used="huggingface_transformer",
                created_by=out_u,
                assignee=inc_u,
                contextual_notes="Worker manually upgraded priority from Medium to High due to short turnaround window.",
            )
            t3_done = Task.objects.create(
                organisation=org_kq,
                shift=shift_active_awaiting,
                handover_report=rep3,
                description="Closed and archived Aircraft Technical Logbook TechLog page #4412 in airline MRO enterprise system.",
                category="Administration",
                confirmed_category="Administration",
                model_suggested_category="Administration",
                status=TaskStatus.COMPLETED,
                priority=TaskPriority.LOW,
                confirmed_priority=TaskPriority.LOW,
                model_suggested_priority=TaskPriority.LOW,
                category_confidence=95.1,
                priority_confidence=93.0,
                confidence_score=94.1,
                nlp_provider_used="huggingface_transformer",
                created_by=out_u,
                assignee=out_u,
            )
            for tk in (t3_crit, t3_prog, t3_done):
                TaskStatusHistory.objects.create(
                    task=tk,
                    changed_by=out_u,
                    previous_status="",
                    new_status=tk.status,
                    previous_priority="",
                    new_priority=tk.priority,
                    comment="Logged in HND-DEMO-003.",
                )

            Notification.objects.create(
                organisation=org_kq,
                recipient=inc_u,
                notification_type=NotificationType.HANDOVER_SUBMITTED,
                related_handover=rep3,
                title="Handover Awaiting Acknowledgment: HND-DEMO-003",
                message=(
                    f"{out_u.full_name} submitted handover report HND-DEMO-003 with 3 tasks "
                    "(2 unresolved, 1 Critical). Please review and formally acknowledge receipt."
                ),
            )
            Notification.objects.create(
                organisation=org_kq,
                recipient=sup_u,
                notification_type=NotificationType.CRITICAL_TASK,
                related_handover=rep3,
                related_task=t3_crit,
                title="Critical Operational Alert: HND-DEMO-003",
                message="Jet fuel seepage reported on 5Y-KZE engine pylon coupling; aircraft grounded pending seal replacement.",
            )

        # Report 4: Editable Draft Handover for Outgoing Worker (`outgoing@shiftsync.ac.ke`)
        rep4, created4 = HandoverReport.objects.update_or_create(
            report_code="HND-DEMO-004",
            defaults={
                "organisation": org_kq,
                "shift": shift_active_draft,
                "submitting_worker": out_u,
                "designated_incoming_worker": inc_u,
                "equipment_status": EquipmentStatusChoice.OPERATIONAL,
                "equipment_details": "All hangar tooling calibrated and operational.",
                "safety_issues": "",
                "has_safety_incident": False,
                "additional_notes": "[DEMO DRAFT] Saved draft ready for additional NLP task logging and formal submission.",
                "status": HandoverStatus.DRAFT,
            },
        )
        if created4:
            t4 = Task.objects.create(
                organisation=org_kq,
                shift=shift_active_draft,
                handover_report=rep4,
                description="Inspect boiler pressure valve on Line 2 after fluctuating readings between 75 and 92 PSI throughout afternoon run.",
                category="Equipment Check",
                confirmed_category="Equipment Check",
                model_suggested_category="Equipment Check",
                status=TaskStatus.PENDING,
                priority=TaskPriority.HIGH,
                confirmed_priority=TaskPriority.HIGH,
                model_suggested_priority=TaskPriority.HIGH,
                category_confidence=91.8,
                priority_confidence=88.4,
                confidence_score=90.1,
                nlp_provider_used="huggingface_transformer",
                created_by=out_u,
                assignee=inc_u,
                contextual_notes="Draft task saved in PostgreSQL.",
            )
            TaskStatusHistory.objects.create(
                task=t4,
                changed_by=out_u,
                previous_status="",
                new_status=TaskStatus.PENDING,
                previous_priority="",
                new_priority=TaskPriority.HIGH,
                comment="Draft task created.",
            )

        AuditEvent.objects.get_or_create(
            organisation=org_kq,
            actor=admin_u,
            action="DEMO_ENVIRONMENT_SEEDED",
            target_type="Organisation",
            target_id=str(org_kq.id),
            defaults={
                "summary": "Seeded demonstration users, shifts, handovers, tasks, and notifications.",
                "ip_address": "127.0.0.1",
            },
        )

        self.stdout.write(
            self.style.SUCCESS(
                "Successfully seeded ShiftSync demonstration records in PostgreSQL!"
            )
        )
        self.stdout.write(
            f"Demo Accounts (Password for all: {DEFAULT_PASSWORD}):\n"
            "  - Admin:      admin@shiftsync.ac.ke\n"
            "  - Supervisor: supervisor@shiftsync.ac.ke\n"
            "  - Outgoing:   outgoing@shiftsync.ac.ke\n"
            "  - Incoming:   incoming@shiftsync.ac.ke\n"
            "  - External:   external@mombasaport.co.ke"
        )
