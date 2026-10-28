import sqlite3
import os
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "data", "shiftsync.db")

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def log_audit(user_name, user_role, action, details=""):
    """Helper to record audit trail entries for Administrator monitoring."""
    try:
        conn = get_connection()
        conn.execute(
            "INSERT INTO audit_logs (user_name, user_role, action, details, created_at) VALUES (?, ?, ?, ?, ?)",
            (user_name, user_role, action, details, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        )
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Error logging audit event: {e}")

def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    # 1. Users Table (Aviation Scoped: Pilots & Aeronautical Engineers)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password TEXT DEFAULT 'password123',
                role TEXT NOT NULL CHECK(role IN (
            'Pilot', 'Aeronautical Engineer', 'Administrator',
            'Captain', 'First Officer', 'Pilot (Captain)', 'First Officer (Pilot)',
            'Licensed Aeronautical Engineer (AME)', 'Avionics Maintenance Engineer',
            'Maintenance Supervisor', 'Flight Operations Supervisor',
            'Outgoing Operator', 'Incoming Operator', 'Supervisor', 'Operator', 'Worker'
        )),
        department TEXT NOT NULL,
        status TEXT DEFAULT 'Active' CHECK(status IN ('Active', 'Inactive')),
        current_shift TEXT DEFAULT 'Line Maint & Flight Ops Shift A',
        last_active DATETIME DEFAULT CURRENT_TIMESTAMP,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # Check if existing users table needs schema migration to support aviation roles
    cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='users'")
    row = cursor.fetchone()
    if row and ("'Pilot'" not in row[0] or "'Aeronautical Engineer'" not in row[0]):
        print("Migrating users table schema to support Pilots and Aeronautical Engineers...")
        cursor.execute("""
        CREATE TABLE users_migrated (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT DEFAULT 'password123',
                    role TEXT NOT NULL CHECK(role IN (
            'Pilot', 'Aeronautical Engineer', 'Administrator',
            'Captain', 'First Officer', 'Pilot (Captain)', 'First Officer (Pilot)',
            'Licensed Aeronautical Engineer (AME)', 'Avionics Maintenance Engineer',
            'Maintenance Supervisor', 'Flight Operations Supervisor',
            'Outgoing Operator', 'Incoming Operator', 'Supervisor', 'Operator', 'Worker'
        )),
            department TEXT NOT NULL,
            status TEXT DEFAULT 'Active' CHECK(status IN ('Active', 'Inactive')),
            current_shift TEXT DEFAULT 'Line Maint & Flight Ops Shift A',
            last_active DATETIME DEFAULT CURRENT_TIMESTAMP,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """)
        cursor.execute("""
        INSERT INTO users_migrated (id, name, email, password, role, department, status, created_at)
        SELECT id, name, email, 'password123', role, department, status, created_at FROM users
        """)
        cursor.execute("DROP TABLE users")
        cursor.execute("ALTER TABLE users_migrated RENAME TO users")
        conn.commit()
        print("Users table successfully migrated to aviation roles.")

    # 2. Shifts Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS shifts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        shift_name TEXT NOT NULL,
        shift_date TEXT NOT NULL,
        start_time TEXT NOT NULL,
        end_time TEXT NOT NULL,
        team TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'Scheduled' CHECK(status IN ('Active', 'Scheduled', 'Completed')),
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # 3. Handover Reports Table (Aviation Scoped with Aircraft Registration, Flight, TechLog, MEL)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS handover_reports (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        report_code TEXT UNIQUE NOT NULL,
        shift_id INTEGER NOT NULL,
        outgoing_operator TEXT NOT NULL,
        incoming_operator TEXT NOT NULL,
        aircraft_tail_number TEXT DEFAULT '5Y-KZE',
        flight_number TEXT DEFAULT 'KQ 102',
        techlog_reference TEXT DEFAULT 'TL-2026-088',
        handover_type TEXT DEFAULT 'Engineer-to-Engineer' CHECK(handover_type IN (
            'Engineer-to-Engineer', 'Pilot-to-Engineer', 'Pilot-to-Pilot', 'General Shift Handover'
        )),
        mel_status TEXT DEFAULT 'Nil Active MEL',
        equipment_status TEXT,
        safety_notes TEXT,
        additional_notes TEXT,
        status TEXT NOT NULL DEFAULT 'Pending Review' CHECK(status IN ('Draft', 'Pending Review', 'Acknowledged', 'Flagged')),
        submitted_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        acknowledged_at DATETIME,
        acknowledged_by TEXT,
        FOREIGN KEY (shift_id) REFERENCES shifts(id)
    )
    """)

    # Add missing aviation columns to handover_reports if table already existed
    cursor.execute("PRAGMA table_info(handover_reports)")
    existing_cols = [c[1] for c in cursor.fetchall()]
    if "aircraft_tail_number" not in existing_cols:
        cursor.execute("ALTER TABLE handover_reports ADD COLUMN aircraft_tail_number TEXT DEFAULT '5Y-KZE'")
    if "flight_number" not in existing_cols:
        cursor.execute("ALTER TABLE handover_reports ADD COLUMN flight_number TEXT DEFAULT 'KQ 102'")
    if "techlog_reference" not in existing_cols:
        cursor.execute("ALTER TABLE handover_reports ADD COLUMN techlog_reference TEXT DEFAULT 'TL-2026-088'")
    if "handover_type" not in existing_cols:
        cursor.execute("ALTER TABLE handover_reports ADD COLUMN handover_type TEXT DEFAULT 'Engineer-to-Engineer'")
    if "mel_status" not in existing_cols:
        cursor.execute("ALTER TABLE handover_reports ADD COLUMN mel_status TEXT DEFAULT 'Nil Active MEL'")

    # 4. Tasks Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        report_id INTEGER,
        task_name TEXT NOT NULL,
        assigned_to TEXT NOT NULL,
        category TEXT NOT NULL CHECK(category IN ('Equipment Check', 'Maintenance', 'Safety & Compliance', 'Operations', 'Administration', 'General')),
        priority TEXT NOT NULL CHECK(priority IN ('Critical', 'High', 'Medium', 'Low')),
        due_date TEXT,
        status TEXT NOT NULL DEFAULT 'Pending' CHECK(status IN ('Pending', 'Open', 'In Progress', 'Completed')),
        aircraft_tail_number TEXT DEFAULT '5Y-KZE',
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (report_id) REFERENCES handover_reports(id) ON DELETE SET NULL
    )
    """)

    # Add aircraft_tail_number to tasks if missing
    cursor.execute("PRAGMA table_info(tasks)")
    task_cols = [c[1] for c in cursor.fetchall()]
    if "aircraft_tail_number" not in task_cols:
        cursor.execute("ALTER TABLE tasks ADD COLUMN aircraft_tail_number TEXT DEFAULT '5Y-KZE'")

    # 5. Notifications Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS notifications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        timestamp_text TEXT NOT NULL,
        type TEXT DEFAULT 'info',
        is_read INTEGER DEFAULT 0,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # 6. Audit & Activity Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS audit_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_name TEXT NOT NULL,
        user_role TEXT NOT NULL,
        action TEXT NOT NULL,
        details TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)

    conn.commit()

    # Seed Initial Data if empty
    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] == 0:
        print("Seeding initial database records for Aviation (Pilots & Aeronautical Engineers)...")
        
        # Seed Aviation Users
        users_seed = [
            ("John Doe", "john@shiftsync.local", "password123", "Pilot", "Flight Operations - B787 Fleet"),
            ("Michael Chang", "michael@shiftsync.local", "password123", "Aeronautical Engineer", "JKIA Line Maintenance (Hangar 1)"),
            ("Amina Noor", "amina@shiftsync.local", "password123", "Pilot", "Flight Operations - E190 Fleet"),
            ("Sarah Jenkins", "sarah@shiftsync.local", "password123", "Aeronautical Engineer", "Fleet Airworthiness & CAMO"),
            ("Emily Watson", "admin@shiftsync.local", "password123", "Administrator", "Flight Operations & Engineering IT"),
            ("David Miller", "david@shiftsync.local", "password123", "Aeronautical Engineer", "Avionics Workshop JKIA")
        ]
        cursor.executemany("INSERT INTO users (name, email, password, role, department) VALUES (?, ?, ?, ?, ?)", users_seed)

        # Seed Aviation Shifts
        shifts_seed = [
            ("Line Maint & Flight Ops Shift A", "2026-10-25", "06:00", "18:00", "Line Crew A (B787-8)", "Active"),
            ("Night Turnaround & Defect Rectification B", "2026-10-24", "18:00", "06:00", "Avionics & Line Crew B", "Completed"),
            ("Transit Ramp Check Shift C", "2026-10-26", "06:00", "18:00", "Line Crew C (E190)", "Scheduled"),
            ("Emergency AOG Standby Shift A", "2026-10-25", "18:00", "06:00", "Rapid Response Engineering Crew", "Scheduled")
        ]
        cursor.executemany("INSERT INTO shifts (shift_name, shift_date, start_time, end_time, team, status) VALUES (?, ?, ?, ?, ?, ?)", shifts_seed)

        # Seed Aviation Handover Reports
        reports_seed = [
            ("HO-2026-088", 1, "John Doe", "Michael Chang", "5Y-KZE", "KQ 102", "TL-2026-088", "Pilot-to-Engineer",
             "MEL Cat C 21-31-01 (Cabin Recirc Fan)",
             "Left Engine (Rolls-Royce Trent 1000) vibration parameter verified at 0.8 IPS. APU generator sync tested nominal at 400Hz. Hydraulic System B pressure steady at 3,020 PSI.",
             "Flight deck pre-flight walkaround completed; wheel chocks and landing gear safety pins verified. FOD sweep completed at Gate 4.",
             "TechLog page #4412 signed off. MEL Cat C 21-31-01 cabin recirculation fan inspection deferred with KCAA flight ops authorization.",
             "Pending Review", datetime.now().strftime("%Y-%m-%d %H:%M"), None, None),

            ("HO-2026-087", 2, "Sarah Jenkins", "John Doe", "5Y-FFF", "KQ 504", "TL-2026-087", "Engineer-to-Engineer",
             "Nil Active MEL",
             "Auxiliary Power Unit APU-04 running nominal. Ground power cart cable inspected and load-tested. Nose gear tire pressure at 195 PSI.",
             "Zero ramp safety incidents reported on Sector 2. Foreign Object Debris (FOD) clearance verified before aircraft docking.",
             "All night transit clearances verified with Flight Dispatch. Certificate of Release to Service (CRS) signed off.",
             "Acknowledged", "2026-10-24 05:55", "2026-10-24 06:10", "John Doe"),

            ("HO-2026-086", 1, "Michael Chang", "Sarah Jenkins", "5Y-KZB", "KQ 310", "TL-2026-086", "Engineer-to-Engineer",
             "Nil Active MEL",
             "Main hydraulic reservoir pressurized to 3,000 PSI without external leakage. Pitot-static probe heating elements tested within resistance spec.",
             "Hangar bay fire safety equipment and emergency eyewash stations inspected.",
             "Torque wrench calibration verified and logged in maintenance stores.",
             "Acknowledged", "2026-10-23 17:50", "2026-10-23 18:05", "Sarah Jenkins")
        ]
        cursor.executemany("""
        INSERT INTO handover_reports (report_code, shift_id, outgoing_operator, incoming_operator, aircraft_tail_number, flight_number, techlog_reference, handover_type, mel_status, equipment_status, safety_notes, additional_notes, status, submitted_at, acknowledged_at, acknowledged_by)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, reports_seed)

        # Seed Aviation Tasks
        tasks_seed = [
            (1, "Inspect B787 Left Engine Oil & Pressure Sensor", "John Doe", "Equipment Check", "High", "Today, 18:00", "In Progress", "5Y-KZE"),
            (1, "Sign-off KCAA Certificate of Release to Service (CRS)", "Sarah Jenkins", "Safety & Compliance", "Critical", "Oct 27, 2026", "Pending", "5Y-KZE"),
            (2, "APU Starter Generator Voltage Verification", "Michael Chang", "Equipment Check", "High", "Oct 26, 2026", "Completed", "5Y-FFF"),
            (None, "Update Aircraft Technical Logbook (TechLog) Section 4", "Sarah Jenkins", "Administration", "Low", "Oct 28, 2026", "Pending", "5Y-FFF"),
            (None, "Calibrate Pitot-Static Sensor Probe #2", "John Doe", "Equipment Check", "Medium", "Oct 29, 2026", "Pending", "5Y-KZB"),
            (None, "Daily Backup of Flight Dispatch & Telemetry", "System Auto", "Administration", "Low", "Everyday, 23:59", "Completed", "Fleet Wide")
        ]
        cursor.executemany("""
        INSERT INTO tasks (report_id, task_name, assigned_to, category, priority, due_date, status, aircraft_tail_number)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, tasks_seed)

        # Seed Aviation Notifications
        notifs_seed = [
            ("Flight KQ 102 (5Y-KZE) TechLog debrief handover submitted by Capt. John Doe", "10 mins ago", "handover", 0),
            ("Task #124 'APU Starter Generator Voltage Verification' signed off by Eng. Michael Chang", "1 hour ago", "task", 0),
            ("Critical Airworthiness Alert: Engine vibration parameter threshold cleared on B787 #5Y-KZE", "2 hours ago", "alert", 0),
            ("Transit Ramp Schedule updated for E190 fleet by Supervisor Sarah Jenkins", "Yesterday, 18:30", "schedule", 1),
            ("Mandatory Pre-Flight Oxygen & Mask Inspection Checklist generated for all Flight Crew", "Oct 24, 2026", "safety", 1),
            ("Automated ACARS & Flight Telemetry archive synchronization completed", "Oct 23, 2026", "system", 1)
        ]
        cursor.executemany("INSERT INTO notifications (title, timestamp_text, type, is_read) VALUES (?, ?, ?, ?)", notifs_seed)

        # Seed Aviation Audit Trail
        initial_audit = [
            ("John Doe", "Pilot", "Pre-Flight Login", "Signed into Line Maint & Flight Ops Shift A (B787 Fleet 5Y-KZE)", "2026-10-01 06:05:00"),
            ("John Doe", "Pilot", "NLP TechLog Analysis", "Processed TechLog #4412 snag report - 3 maintenance tasks detected with 99% confidence", "2026-10-01 07:15:22"),
            ("Michael Chang", "Aeronautical Engineer", "Task Completed", "Rectified snag: 'APU Starter Generator Voltage Verification' on 5Y-FFF", "2026-10-01 08:30:10"),
            ("John Doe", "Pilot", "Handover Submitted", "Filed Flight KQ 102 Handover Report HO-2026-088 to incoming AME Michael Chang", "2026-10-01 08:45:00"),
            ("Emily Watson", "Administrator", "Fleet Monitoring", "Inspected Line Maintenance Crew A & B task completion rate across JKIA gates", "2026-10-01 09:00:15")
        ]
        cursor.executemany("INSERT INTO audit_logs (user_name, user_role, action, details, created_at) VALUES (?, ?, ?, ?, ?)", initial_audit)

        conn.commit()
        print("Database seeded successfully with aviation records.")
    else:
        # If users exist, ensure aviation roles/departments and records are upgraded
        cursor.execute("UPDATE users SET role = 'Pilot', department = 'Flight Operations - B787 Fleet' WHERE email = 'john@shiftsync.local'")
        cursor.execute("UPDATE users SET role = 'Aeronautical Engineer', department = 'JKIA Line Maintenance (Hangar 1)' WHERE email = 'michael@shiftsync.local'")
        cursor.execute("UPDATE users SET role = 'Aeronautical Engineer', department = 'Fleet Airworthiness & CAMO' WHERE email = 'sarah@shiftsync.local'")
        cursor.execute("UPDATE users SET role = 'Aeronautical Engineer', department = 'Avionics Workshop JKIA' WHERE email = 'david@shiftsync.local'")
        cursor.execute("UPDATE users SET role = 'Administrator', department = 'Flight Operations & Engineering IT' WHERE email = 'admin@shiftsync.local'")
        
        # Add Amina Noor if not present
        cursor.execute("SELECT id FROM users WHERE email = 'amina@shiftsync.local'")
        if not cursor.fetchone():
            cursor.execute("INSERT INTO users (name, email, password, role, department) VALUES ('Amina Noor', 'amina@shiftsync.local', 'password123', 'Pilot', 'Flight Operations - E190 Fleet')")

        # Update shifts with aviation titles if still on generic titles
        cursor.execute("UPDATE shifts SET shift_name = 'Line Maint & Flight Ops Shift A', team = 'Line Crew A (B787-8)' WHERE id = 1")
        cursor.execute("UPDATE shifts SET shift_name = 'Night Turnaround & Defect Rectification B', team = 'Avionics & Line Crew B' WHERE id = 2")
        cursor.execute("UPDATE shifts SET shift_name = 'Transit Ramp Check Shift C', team = 'Line Crew C (E190)' WHERE id = 3")
        cursor.execute("UPDATE shifts SET shift_name = 'Emergency AOG Standby Shift A', team = 'Rapid Response Engineering Crew' WHERE id = 4")

        # Update handover_reports with aviation metadata
        cursor.execute("""
        UPDATE handover_reports 
        SET aircraft_tail_number = '5Y-KZE', flight_number = 'KQ 102', techlog_reference = 'TL-2026-088',
            handover_type = 'Pilot-to-Engineer', mel_status = 'MEL Cat C 21-31-01 (Cabin Recirc Fan)'
        WHERE report_code = 'HO-2026-088'
        """)
        cursor.execute("""
        UPDATE handover_reports 
        SET aircraft_tail_number = '5Y-FFF', flight_number = 'KQ 504', techlog_reference = 'TL-2026-087',
            handover_type = 'Engineer-to-Engineer', mel_status = 'Nil Active MEL'
        WHERE report_code = 'HO-2026-087'
        """)
        cursor.execute("""
        UPDATE handover_reports 
        SET aircraft_tail_number = '5Y-KZB', flight_number = 'KQ 310', techlog_reference = 'TL-2026-086',
            handover_type = 'Engineer-to-Engineer', mel_status = 'Nil Active MEL'
        WHERE report_code = 'HO-2026-086'
        """)

        # Update initial tasks to aviation context
        cursor.execute("UPDATE tasks SET task_name = 'Inspect B787 Left Engine Oil & Pressure Sensor', aircraft_tail_number = '5Y-KZE' WHERE id = 1")
        cursor.execute("UPDATE tasks SET task_name = 'Sign-off KCAA Certificate of Release to Service (CRS)', aircraft_tail_number = '5Y-KZE' WHERE id = 2")
        cursor.execute("UPDATE tasks SET task_name = 'APU Starter Generator Voltage Verification', aircraft_tail_number = '5Y-FFF' WHERE id = 3")
        cursor.execute("UPDATE tasks SET task_name = 'Update Aircraft Technical Logbook (TechLog) Section 4', aircraft_tail_number = '5Y-FFF' WHERE id = 4")
        cursor.execute("UPDATE tasks SET task_name = 'Calibrate Pitot-Static Sensor Probe #2', aircraft_tail_number = '5Y-KZB' WHERE id = 5")
        cursor.execute("UPDATE tasks SET task_name = 'Daily Backup of Flight Dispatch & Telemetry', aircraft_tail_number = 'Fleet Wide' WHERE id = 6")

        conn.commit()
        print("Existing database records successfully updated to Aviation configuration.")

    conn.close()

if __name__ == "__main__":
    init_db()
    print(f"SQLite database initialized at: {DB_PATH}")
