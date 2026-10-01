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
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
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
            # 0. Health Check Endpoint
            if path == "/api/health":
                self.send_json_response({
                    "status": "healthy",
                    "system": "ShiftSync Operational Handover Engine",
                    "timestamp": datetime.now().isoformat(),
                    "database": "connected",
                    "models_loaded": nlp_engine is not None
                })
                return

            # 1. Dashboard Stats
            elif path == "/api/dashboard-stats":
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

            # 2. Worker Monitoring Data (For Administrator View)
            elif path == "/api/worker-monitoring":
                # Fetch all users
                cursor.execute("""
                SELECT id, name, email, role, department, status, current_shift, last_active, created_at
                FROM users
                ORDER BY CASE WHEN role LIKE '%Admin%' THEN 2 ELSE 1 END, id ASC
                """)
                all_users = [dict(row) for row in cursor.fetchall()]

                workers_data = []
                for u in all_users:
                    u_name = u["name"]
                    # Total tasks assigned to this worker
                    cursor.execute("SELECT COUNT(*) FROM tasks WHERE assigned_to = ?", (u_name,))
                    tot_tasks = cursor.fetchone()[0]

                    # Completed tasks
                    cursor.execute("SELECT COUNT(*) FROM tasks WHERE assigned_to = ? AND status = 'Completed'", (u_name,))
                    comp_tasks = cursor.fetchone()[0]

                    # In-progress / Pending tasks
                    cursor.execute("SELECT COUNT(*) FROM tasks WHERE assigned_to = ? AND status != 'Completed'", (u_name,))
                    pend_tasks = cursor.fetchone()[0]

                    rate = round((comp_tasks / tot_tasks * 100), 1) if tot_tasks > 0 else 100.0

                    # Latest Handover Report submitted
                    cursor.execute("""
                    SELECT report_code, status, submitted_at, equipment_status, safety_notes
                    FROM handover_reports
                    WHERE outgoing_operator = ?
                    ORDER BY id DESC LIMIT 1
                    """, (u_name,))
                    h_row = cursor.fetchone()
                    latest_handover = dict(h_row) if h_row else None

                    u["task_stats"] = {
                        "total": tot_tasks,
                        "completed": comp_tasks,
                        "pending": pend_tasks,
                        "completion_rate": rate
                    }
                    u["latest_handover"] = latest_handover
                    workers_data.append(u)

                # Filter worker-only list for aggregations
                workers_only = [w for w in workers_data if "Admin" not in w["role"]]
                active_workers_count = len([w for w in workers_only if w["status"] == "Active"])
                total_worker_tasks = sum(w["task_stats"]["total"] for w in workers_only)
                completed_worker_tasks = sum(w["task_stats"]["completed"] for w in workers_only)
                overall_rate = round((completed_worker_tasks / total_worker_tasks * 100), 1) if total_worker_tasks > 0 else 0

                cursor.execute("SELECT COUNT(*) FROM handover_reports WHERE status = 'Pending Review'")
                pending_handovers = cursor.fetchone()[0]

                # Fetch live audit trail
                cursor.execute("SELECT * FROM audit_logs ORDER BY id DESC LIMIT 25")
                audit_trail = [dict(row) for row in cursor.fetchall()]

                self.send_json_response({
                    "metrics": {
                        "total_workers": len(workers_only),
                        "active_workers": active_workers_count,
                        "total_tasks": total_worker_tasks,
                        "completed_tasks": completed_worker_tasks,
                        "completion_rate": overall_rate,
                        "pending_handovers": pending_handovers
                    },
                    "workers": workers_data,
                    "audit_trail": audit_trail
                })
                return

            # 3. Shifts
            elif path == "/api/shifts":
                cursor.execute("SELECT * FROM shifts ORDER BY shift_date DESC, start_time DESC")
                shifts = [dict(row) for row in cursor.fetchall()]
                self.send_json_response({"shifts": shifts})
                return

            # 4. Handover Reports
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

            # 5. Tasks
            elif path == "/api/tasks":
                cursor.execute("SELECT * FROM tasks ORDER BY id DESC")
                tasks = [dict(row) for row in cursor.fetchall()]
                self.send_json_response({"tasks": tasks})
                return

            # 6. Users
            elif path == "/api/users":
                cursor.execute("SELECT id, name, email, role, department, status, current_shift, last_active, created_at FROM users ORDER BY id ASC")
                users = [dict(row) for row in cursor.fetchall()]
                self.send_json_response({"users": users})
                return

            # 7. Notifications
            elif path == "/api/notifications":
                cursor.execute("SELECT * FROM notifications ORDER BY id DESC LIMIT 20")
                notifs = [dict(row) for row in cursor.fetchall()]
                self.send_json_response({"notifications": notifs})
                return

            # 8. Audit Logs
            elif path == "/api/audit-logs":
                cursor.execute("SELECT * FROM audit_logs ORDER BY id DESC LIMIT 50")
                logs = [dict(row) for row in cursor.fetchall()]
                self.send_json_response({"audit_logs": logs})
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

        # 0. User Signup
        if path == "/api/signup":
            name = data.get("name", "").strip()
            email = data.get("email", "").strip().lower()
            password = data.get("password", "password123").strip()
            role = data.get("role", "Worker").strip()
            department = data.get("department", "Operations Crew").strip()

            if not name or not email:
                self.send_json_response({"error": "Full name and email are required."}, 400)
                return

            # Validate role
            valid_roles = ["Worker", "Operator", "Outgoing Operator", "Incoming Operator", "Supervisor", "Administrator"]
            if role not in valid_roles:
                role = "Worker"

            conn = database.get_connection()
            cursor = conn.cursor()
            try:
                cursor.execute("SELECT id FROM users WHERE LOWER(email) = ?", (email,))
                if cursor.fetchone():
                    self.send_json_response({"error": f"An account with email '{email}' already exists. Please log in."}, 409)
                    return

                cursor.execute("""
                INSERT INTO users (name, email, password, role, department, status, current_shift)
                VALUES (?, ?, ?, ?, ?, 'Active', 'Day Shift A')
                """, (name, email, password, role, department))
                conn.commit()
                user_id = cursor.lastrowid

                # Record in audit trail & notifications
                database.log_audit(name, role, "Account Registered", f"New user registered under department '{department}'")
                cursor.execute("""
                INSERT INTO notifications (title, timestamp_text, type, is_read)
                VALUES (?, 'Just now', 'system', 0)
                """, (f"New {role} account registered: {name} ({department})",))
                conn.commit()

                user_profile = {
                    "id": user_id,
                    "name": name,
                    "email": email,
                    "role": role,
                    "department": department,
                    "status": "Active"
                }
                self.send_json_response({
                    "message": "Account created successfully.",
                    "user": user_profile
                }, 201)
                return
            except Exception as e:
                import traceback
                traceback.print_exc()
                self.send_json_response({"error": str(e)}, 500)
                return
            finally:
                conn.close()

        # 1. User Login
        if path == "/api/login":
            email = data.get("email", "").strip().lower()
            password = data.get("password", "").strip()
            role_type = data.get("role_type", "").strip().lower()  # "administrator" or "worker"

            conn = database.get_connection()
            cursor = conn.cursor()
            try:
                if role_type == "administrator" and not email:
                    cursor.execute("SELECT * FROM users WHERE role = 'Administrator' ORDER BY id ASC LIMIT 1")
                elif role_type == "worker" and not email:
                    cursor.execute("SELECT * FROM users WHERE role IN ('Worker', 'Operator', 'Outgoing Operator') ORDER BY id ASC LIMIT 1")
                else:
                    cursor.execute("SELECT * FROM users WHERE LOWER(email) = ?", (email,))

                row = cursor.fetchone()
                if not row:
                    self.send_json_response({"error": "User account not found. Please verify your credentials or create a new account."}, 401)
                    return

                user = dict(row)
                # Update last active timestamp
                cursor.execute("UPDATE users SET last_active = CURRENT_TIMESTAMP WHERE id = ?", (user["id"],))
                conn.commit()

                # Audit log
                database.log_audit(user["name"], user["role"], "User Login", f"Signed into {user['role']} session ({user['department']})")

                # Remove password from response
                user.pop("password", None)
                self.send_json_response({"message": "Login successful", "user": user}, 200)
                return
            except Exception as e:
                import traceback
                traceback.print_exc()
                self.send_json_response({"error": str(e)}, 500)
                return
            finally:
                conn.close()

        # 2. NLP Inference
        if path == "/api/analyze-shift":
            notes = data.get("notes", "")
            user_name = data.get("user", "Shift Worker")
            if not notes.strip():
                self.send_json_response({"error": "Notes cannot be empty"}, 400)
                return
            try:
                response_data = nlp_engine.analyze_shift_log(notes)
                # Audit log for Administrator monitoring
                task_count = len(response_data.get("tasks", []))
                database.log_audit(user_name, "Worker", "NLP Shift Analysis", f"Processed log notes: {task_count} tasks automatically detected & classified")
                self.send_json_response(response_data, 200)
            except Exception as e:
                import traceback
                traceback.print_exc()
                self.send_json_response({"error": str(e)}, 500)
            return

        conn = database.get_connection()
        cursor = conn.cursor()

        try:
            # 3. Add New Shift
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
                database.log_audit("Administrator", "Administrator", "Shift Created", f"Scheduled shift '{name}' for {date} ({team})")
                self.send_json_response({"message": "Shift created successfully", "shift_id": shift_id}, 201)
                return

            # 4. Create Handover Report
            elif path == "/api/handovers":
                shift_id = data.get("shift_id", 1)
                outgoing = data.get("outgoing_operator", "John Doe")
                incoming = data.get("incoming_operator", "Michael Chang")
                equip = data.get("equipment_status", "")
                safety = data.get("safety_notes", "")
                notes = data.get("additional_notes", "")
                tasks = data.get("tasks", [])

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
                database.log_audit(outgoing, "Worker", "Handover Submitted", f"Filed report {report_code} to incoming worker {incoming} ({len(tasks)} tasks attached)")
                self.send_json_response({"message": "Handover report submitted", "report_code": report_code, "report_id": report_id}, 201)
                return

            # 5. Acknowledge Handover Report
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
                database.log_audit(ack_user, "Worker", "Handover Acknowledged", f"Formally signed off and acknowledged handover #{report_code}")
                self.send_json_response({"message": "Handover acknowledged successfully", "report_code": report_code, "acknowledged_at": ack_time})
                return

            # 6. Add Single Task
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
                database.log_audit(assignee, "Worker", "Task Created", f"Assigned task '{name}' (Priority: {prio})")
                self.send_json_response({"message": "Task created", "task_id": task_id}, 201)
                return

            # 7. Toggle Task Status
            elif path.startswith("/api/tasks/") and path.endswith("/toggle"):
                task_id = path.split("/")[3]
                cursor.execute("SELECT task_name, status, assigned_to FROM tasks WHERE id = ?", (task_id,))
                row = cursor.fetchone()
                if row:
                    new_status = "Completed" if row["status"] != "Completed" else "In Progress"
                    cursor.execute("UPDATE tasks SET status = ? WHERE id = ?", (new_status, task_id))
                    conn.commit()
                    database.log_audit(row["assigned_to"], "Worker", "Task Status Updated", f"Task '{row['task_name']}' set to {new_status}")
                    self.send_json_response({"message": "Status updated", "new_status": new_status})
                else:
                    self.send_json_response({"error": "Task not found"}, 404)
                return

            # 8. Add User
            elif path == "/api/users":
                name = data.get("name")
                email = data.get("email")
                role = data.get("role", "Worker")
                dept = data.get("department", "Operations")
                password = data.get("password", "password123")

                cursor.execute("""
                INSERT INTO users (name, email, password, role, department)
                VALUES (?, ?, ?, ?, ?)
                """, (name, email, password, role, dept))
                conn.commit()
                user_id = cursor.lastrowid
                database.log_audit("Administrator", "Administrator", "User Created", f"Created user profile for {name} ({role})")
                self.send_json_response({"message": "User added", "user_id": user_id}, 201)
                return

            # 9. Mark Notifications Read
            elif path == "/api/notifications/mark-read":
                cursor.execute("UPDATE notifications SET is_read = 1")
                conn.commit()
                self.send_json_response({"message": "All notifications marked as read"})
                return

            # 10. Administrator Broadcast Announcement
            elif path == "/api/admin/broadcast":
                message = data.get("message", "Operational priority shift update")
                author = data.get("author", "Administrator")
                cursor.execute("""
                INSERT INTO notifications (title, timestamp_text, type, is_read)
                VALUES (?, 'Just now', 'alert', 0)
                """, (f"[ADMIN DIRECTIVE] {message}",))
                conn.commit()
                database.log_audit(author, "Administrator", "Broadcast Directive", message)
                self.send_json_response({"message": "Operational broadcast dispatched to all shift workers."})
                return

            # 11. Administrator Toggle Worker Status
            elif path == "/api/admin/toggle-worker-status":
                user_id = data.get("user_id")
                cursor.execute("SELECT name, status FROM users WHERE id = ?", (user_id,))
                row = cursor.fetchone()
                if row:
                    new_stat = "Inactive" if row["status"] == "Active" else "Active"
                    cursor.execute("UPDATE users SET status = ? WHERE id = ?", (new_stat, user_id))
                    conn.commit()
                    database.log_audit("Administrator", "Administrator", "Worker Status Update", f"Worker {row['name']} status changed to {new_stat}")
                    self.send_json_response({"message": "Worker status updated", "new_status": new_stat})
                else:
                    self.send_json_response({"error": "Worker not found"}, 404)
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
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
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
