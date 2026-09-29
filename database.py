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

def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    # 1. Users Table (Section 3.4.2 & 3.4.3)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        role TEXT NOT NULL CHECK(role IN ('Outgoing Operator', 'Incoming Operator', 'Supervisor', 'Administrator', 'Operator')),
        department TEXT NOT NULL,
        status TEXT DEFAULT 'Active' CHECK(status IN ('Active', 'Inactive')),
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)

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

    # 3. Handover Reports Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS handover_reports (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        report_code TEXT UNIQUE NOT NULL,
        shift_id INTEGER NOT NULL,
        outgoing_operator TEXT NOT NULL,
        incoming_operator TEXT NOT NULL,
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
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (report_id) REFERENCES handover_reports(id) ON DELETE SET NULL
    )
    """)

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

    conn.commit()

    # Seed Initial Data if empty
    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] == 0:
        print("Seeding initial database records matching Kenya Airways ShiftSync configuration...")
        
        # Seed Users
        users_seed = [
            ("John Doe", "john@shiftsync.local", "Outgoing Operator", "JKIA Ramp Crew A"),
            ("Michael Chang", "michael@shiftsync.local", "Incoming Operator", "Line Maintenance Crew B"),
            ("Sarah Jenkins", "sarah@shiftsync.local", "Supervisor", "Ground Operations JKIA"),
            ("Emily Watson", "admin@shiftsync.local", "Administrator", "KQ IT Systems"),
            ("David Miller", "david@shiftsync.local", "Operator", "Logistics & Cargo")
        ]
        cursor.executemany("INSERT INTO users (name, email, role, department) VALUES (?, ?, ?, ?)", users_seed)

        # Seed Shifts
        shifts_seed = [
            ("Day Shift A", "2026-10-25", "06:00", "18:00", "Crew A", "Active"),
            ("Night Shift B", "2026-10-24", "18:00", "06:00", "Crew B", "Completed"),
            ("Day Shift C", "2026-10-26", "06:00", "18:00", "Crew C", "Scheduled"),
            ("Night Shift A", "2026-10-25", "18:00", "06:00", "Crew A", "Scheduled")
        ]
        cursor.executemany("INSERT INTO shifts (shift_name, shift_date, start_time, end_time, team, status) VALUES (?, ?, ?, ?, ?, ?)", shifts_seed)

        # Seed Handover Reports
        reports_seed = [
            ("HO-2026-088", 1, "John Doe", "Michael Chang", 
             "Boiler Valve #3 tested normal at 78 PSI. Conveyor B sensor inspected; requires zero-point calibration before next production run.",
             "No safety breaches or injuries occurred. Area around Compressor C-101 kept clean and dry.",
             "Keys for tool cabinet B placed in shift locker.", "Pending Review", datetime.now().strftime("%Y-%m-%d %H:%M"), None, None),
            ("HO-2026-087", 2, "Sarah Jenkins", "John Doe",
             "Auxiliary Power Unit APU-04 running nominal. Ground power cart cable inspected.",
             "No safety incidents reported on Ramp Sector 2.",
             "All night transit clearances verified.", "Acknowledged", "2026-10-24 05:55", "2026-10-24 06:10", "John Doe"),
            ("HO-2026-086", 1, "Michael Chang", "Sarah Jenkins",
             "Hydraulic test rig pressurized to 3000 PSI without leakage.",
             "Weekly fire extinguisher inspection logged.",
             "Routine tool check complete.", "Acknowledged", "2026-10-23 17:50", "2026-10-23 18:05", "Sarah Jenkins")
        ]
        cursor.executemany("""
        INSERT INTO handover_reports (report_code, shift_id, outgoing_operator, incoming_operator, equipment_status, safety_notes, additional_notes, status, submitted_at, acknowledged_at, acknowledged_by)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, reports_seed)

        # Seed Tasks
        tasks_seed = [
            (1, "Inspect Boiler Pressure Valve", "John Doe", "Equipment Check", "High", "Today, 18:00", "In Progress"),
            (1, "Safety Drill Log Upload", "Sarah Jenkins", "Safety & Compliance", "Medium", "Oct 27, 2026", "Pending"),
            (2, "Generator Fuel Level Verification", "Michael Chang", "Equipment Check", "High", "Oct 26, 2026", "Completed"),
            (None, "Update Shift Logbook Section 4", "Sarah Jenkins", "Administration", "Low", "Oct 28, 2026", "Pending"),
            (None, "Calibrate Water Flow Sensor #2", "John Doe", "Equipment Check", "Medium", "Oct 29, 2026", "Pending"),
            (None, "Daily Backup of SCADA Telemetry", "System Auto", "Administration", "Low", "Everyday, 23:59", "Completed")
        ]
        cursor.executemany("""
        INSERT INTO tasks (report_id, task_name, assigned_to, category, priority, due_date, status)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """, tasks_seed)

        # Seed Notifications
        notifs_seed = [
            ("New handover report submitted by John Doe for Day Shift A", "10 mins ago", "handover", 0),
            ("Task #124 'Verify generator fuel reserve level' marked as completed by Michael Chang", "1 hour ago", "task", 0),
            ("Critical Alert: Boiler pressure threshold warning resolved on Valve #3", "2 hours ago", "alert", 0),
            ("Night Shift B schedule has been updated by Supervisor Sarah Jenkins", "Yesterday, 18:30", "schedule", 1),
            ("Weekly Safety Drill Checklist has been generated for all Crew A operators", "Oct 24, 2026", "safety", 1),
            ("System maintenance completed on database logging telemetry servers", "Oct 23, 2026", "system", 1)
        ]
        cursor.executemany("INSERT INTO notifications (title, timestamp_text, type, is_read) VALUES (?, ?, ?, ?)", notifs_seed)

        conn.commit()
        print("Database seeded successfully with initial ShiftSync data.")

    conn.close()

if __name__ == "__main__":
    init_db()
    print(f"SQLite database initialized at: {DB_PATH}")
