import http.server
import socketserver
import json
import os
import urllib.parse
from datetime import datetime
from predict import ShiftSyncNLP
import database

PORT = 8000
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Ensure database is initialized
database.init_db()

# Initialize the trained NLP model
print("Loading ShiftSync NLP models...")
nlp_engine = ShiftSyncNLP()
print("ShiftSync NLP engine initialized successfully.")

class ShiftSyncRequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=BASE_DIR, **kwargs)

    def send_json_response(self, data, status_code=200):
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode("utf-8"))

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        # Static routing
        if path == "/" or path == "/index.html":
            self.path = "/shiftsync_core_system.html"
            return super().do_GET()

        conn = database.get_connection()
        cursor = conn.cursor()

        try:
            # 1. Dashboard Stats
            if path == "/api/dashboard-stats":
                cursor.execute("SELECT COUNT(*) FROM handover_reports WHERE status = 'Pending Review'")
                pending_handovers = cursor.fetchone()[0]

                cursor.execute("SELECT COUNT(*) FROM tasks WHERE status != 'Completed'")
                incomplete_tasks = cursor.fetchone()[0]

                cursor.execute("SELECT COUNT(*) FROM notifications WHERE is_read = 0")
                unread_alerts = cursor.fetchone()[0]

                cursor.execute("SELECT * FROM shifts WHERE status = 'Active' LIMIT 1")
                active_shift_row = cursor.fetchone()
                active_shift = dict(active_shift_row) if active_shift_row else None

                self.send_json_response({
                    "pending_handovers": pending_handovers,
                    "incomplete_tasks": incomplete_tasks,
                    "unread_alerts": unread_alerts,
                    "active_shift": active_shift
                })
                return

            # 2. Shifts
            elif path == "/api/shifts":
                cursor.execute("SELECT * FROM shifts ORDER BY shift_date DESC, start_time DESC")
                shifts = [dict(row) for row in cursor.fetchall()]
                self.send_json_response({"shifts": shifts})
                return

            # 3. Handover Reports
            elif path == "/api/handovers":
                cursor.execute("""
                SELECT h.*, s.shift_name, s.shift_date, s.team 
                FROM handover_reports h
                JOIN shifts s ON h.shift_id = s.id
                ORDER BY h.submitted_at DESC
                """)
                reports = [dict(row) for row in cursor.fetchall()]
                self.send_json_response({"handovers": reports})
                return

            # 4. Tasks
            elif path == "/api/tasks":
                cursor.execute("SELECT * FROM tasks ORDER BY id DESC")
                tasks = [dict(row) for row in cursor.fetchall()]
                self.send_json_response({"tasks": tasks})
                return

            # 5. Users
            elif path == "/api/users":
                cursor.execute("SELECT * FROM users ORDER BY id ASC")
                users = [dict(row) for row in cursor.fetchall()]
                self.send_json_response({"users": users})
                return

            # 6. Notifications
            elif path == "/api/notifications":
                cursor.execute("SELECT * FROM notifications ORDER BY id DESC LIMIT 20")
                notifs = [dict(row) for row in cursor.fetchall()]
                self.send_json_response({"notifications": notifs})
                return

        except Exception as e:
            import traceback
            traceback.print_exc()
            self.send_json_response({"error": str(e)}, 500)
            return
        finally:
            conn.close()

        # Fallback to static file serving
        return super().do_GET()

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length) if content_length > 0 else b"{}"

        try:
            data = json.loads(body.decode("utf-8")) if body else {}
        except Exception:
            data = {}

        # 1. NLP Inference
        if path == "/api/analyze-shift":
            notes = data.get("notes", "")
            if not notes.strip():
                self.send_json_response({"error": "Notes cannot be empty"}, 400)
                return
            try:
                response_data = nlp_engine.analyze_shift_log(notes)
                self.send_json_response(response_data, 200)
            except Exception as e:
                import traceback
                traceback.print_exc()
                self.send_json_response({"error": str(e)}, 500)
            return

        conn = database.get_connection()
        cursor = conn.cursor()

        try:
            # 2. Add New Shift
            if path == "/api/shifts":
                name = data.get("shift_name")
                date = data.get("shift_date")
                start = data.get("start_time")
                end = data.get("end_time")
                team = data.get("team")
                status = data.get("status", "Scheduled")

                cursor.execute("""
                INSERT INTO shifts (shift_name, shift_date, start_time, end_time, team, status)
                VALUES (?, ?, ?, ?, ?, ?)
                """, (name, date, start, end, team, status))
                conn.commit()
                shift_id = cursor.lastrowid
                self.send_json_response({"message": "Shift created successfully", "shift_id": shift_id}, 201)
                return

            # 3. Create Handover Report
            elif path == "/api/handovers":
                shift_id = data.get("shift_id", 1)
                outgoing = data.get("outgoing_operator", "John Doe")
                incoming = data.get("incoming_operator", "Michael Chang")
                equip = data.get("equipment_status", "")
                safety = data.get("safety_notes", "")
                notes = data.get("additional_notes", "")
                tasks = data.get("tasks", [])

                # Generate code e.g. HO-2026-089
                cursor.execute("SELECT COUNT(*) FROM handover_reports")
                cnt = cursor.fetchone()[0] + 89
                report_code = f"HO-2026-{cnt:03d}"

                cursor.execute("""
                INSERT INTO handover_reports 
                (report_code, shift_id, outgoing_operator, incoming_operator, equipment_status, safety_notes, additional_notes, status, submitted_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, 'Pending Review', ?)
                """, (report_code, shift_id, outgoing, incoming, equip, safety, notes, datetime.now().strftime("%Y-%m-%d %H:%M")))
                report_id = cursor.lastrowid

                # Save associated tasks
                for t in tasks:
                    t_name = t.get("task") or t.get("name")
                    t_cat = t.get("category", "General")
                    t_prio = t.get("priority", "Medium")
                    t_stat = t.get("status", "Pending")
                    cursor.execute("""
                    INSERT INTO tasks (report_id, task_name, assigned_to, category, priority, due_date, status)
                    VALUES (?, ?, ?, ?, ?, 'Today, Shift End', ?)
                    """, (report_id, t_name, incoming, t_cat, t_prio, t_stat))

                # Create Notification
                cursor.execute("""
                INSERT INTO notifications (title, timestamp_text, type, is_read)
                VALUES (?, 'Just now', 'handover', 0)
                """, (f"New handover report {report_code} submitted by {outgoing}",))

                conn.commit()
                self.send_json_response({"message": "Handover report submitted", "report_code": report_code, "report_id": report_id}, 201)
                return

            # 4. Acknowledge Handover Report
            elif path.startswith("/api/handovers/") and path.endswith("/acknowledge"):
                report_code = path.split("/")[3]
                ack_user = data.get("user", "Michael Chang")
                ack_time = datetime.now().strftime("%Y-%m-%d %H:%M")

                cursor.execute("""
                UPDATE handover_reports 
                SET status = 'Acknowledged', acknowledged_at = ?, acknowledged_by = ?
                WHERE report_code = ? OR id = ?
                """, (ack_time, ack_user, report_code, report_code))
                
                cursor.execute("""
                INSERT INTO notifications (title, timestamp_text, type, is_read)
                VALUES (?, 'Just now', 'handover', 0)
                """, (f"Handover report #{report_code} formally acknowledged by {ack_user}",))

                conn.commit()
                self.send_json_response({"message": "Handover acknowledged successfully", "report_code": report_code, "acknowledged_at": ack_time})
                return

            # 5. Add Single Task
            elif path == "/api/tasks":
                name = data.get("task_name")
                assignee = data.get("assigned_to", "John Doe")
                cat = data.get("category", "Operations")
                prio = data.get("priority", "Medium")
                due = data.get("due_date", "Today, 18:00")
                stat = data.get("status", "Pending")

                cursor.execute("""
                INSERT INTO tasks (task_name, assigned_to, category, priority, due_date, status)
                VALUES (?, ?, ?, ?, ?, ?)
                """, (name, assignee, cat, prio, due, stat))
                conn.commit()
                task_id = cursor.lastrowid
                self.send_json_response({"message": "Task created", "task_id": task_id}, 201)
                return

            # 6. Toggle Task Status
            elif path.startswith("/api/tasks/") and path.endswith("/toggle"):
                task_id = path.split("/")[3]
                cursor.execute("SELECT status FROM tasks WHERE id = ?", (task_id,))
                row = cursor.fetchone()
                if row:
                    new_status = "Completed" if row["status"] != "Completed" else "In Progress"
                    cursor.execute("UPDATE tasks SET status = ? WHERE id = ?", (new_status, task_id))
                    conn.commit()
                    self.send_json_response({"message": "Status updated", "new_status": new_status})
                else:
                    self.send_json_response({"error": "Task not found"}, 404)
                return

            # 7. Add User
            elif path == "/api/users":
                name = data.get("name")
                email = data.get("email")
                role = data.get("role", "Operator")
                dept = data.get("department", "Operations")

                cursor.execute("""
                INSERT INTO users (name, email, role, department)
                VALUES (?, ?, ?, ?)
                """, (name, email, role, dept))
                conn.commit()
                user_id = cursor.lastrowid
                self.send_json_response({"message": "User added", "user_id": user_id}, 201)
                return

            # 8. Mark Notifications Read
            elif path == "/api/notifications/mark-read":
                cursor.execute("UPDATE notifications SET is_read = 1")
                conn.commit()
                self.send_json_response({"message": "All notifications marked as read"})
                return

        except Exception as e:
            import traceback
            traceback.print_exc()
            self.send_json_response({"error": str(e)}, 500)
            return
        finally:
            conn.close()

        self.send_json_response({"error": "Endpoint not found"}, 404)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, GET, OPTIONS, DELETE, PUT")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

if __name__ == "__main__":
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", PORT), ShiftSyncRequestHandler) as httpd:
        print("=" * 60)
        print(f"ShiftSync Database-Connected Full-Stack Server Running!")
        print(f"Database: SQLite ({database.DB_PATH})")
        print(f"URL: http://localhost:{PORT}")
        print("=" * 60)
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down server.")
