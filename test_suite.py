import unittest
import json
import time
import os
import sqlite3
import urllib.request
from predict import ShiftSyncNLP
import database

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
API_BASE = "http://localhost:8000"

# Collection to store test execution logs for Chapter 4 documentation
test_records = []

def record_test(test_id, module, description, test_input, expected, actual, passed, elapsed_ms):
    test_records.append({
        "id": test_id,
        "module": module,
        "description": description,
        "input": str(test_input)[:45] + ("..." if len(str(test_input)) > 45 else ""),
        "expected": expected,
        "actual": actual,
        "status": "PASS" if passed else "FAIL",
        "time_ms": f"{elapsed_ms:.1f}ms"
    })

class TestShiftSyncNLP(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.nlp = ShiftSyncNLP()

    def test_nlp_01_equipment_check(self):
        t0 = time.perf_counter()
        text = "Checked boiler pressure valve on Line 2, fluctuating readings observed."
        res = self.nlp.analyze_task(text)
        elapsed = (time.perf_counter() - t0) * 1000
        passed = (res["category"] == "Equipment Check" and res["priority"] in ["High", "Critical"])
        record_test("TC-NLP-01", "NLP Model", "Equipment check categorization", text, "Equipment Check / High", f"{res['category']} / {res['priority']}", passed, elapsed)
        self.assertTrue(passed)

    def test_nlp_02_critical_safety(self):
        t0 = time.perf_counter()
        text = "Major chemical spill reported in Warehouse Sector B, evacuated personnel."
        res = self.nlp.analyze_task(text)
        elapsed = (time.perf_counter() - t0) * 1000
        passed = (res["category"] == "Safety & Compliance" and res["priority"] == "Critical")
        record_test("TC-NLP-02", "NLP Model", "Critical safety incident detection", text, "Safety & Compliance / Critical", f"{res['category']} / {res['priority']}", passed, elapsed)
        self.assertTrue(passed)

    def test_nlp_03_maintenance(self):
        t0 = time.perf_counter()
        text = "Replaced faulty sensor and worn conveyor belt bearing in packaging area."
        res = self.nlp.analyze_task(text)
        elapsed = (time.perf_counter() - t0) * 1000
        passed = (res["category"] in ["Maintenance", "Equipment Check"] and res["priority"] in ["High", "Critical"])
        record_test("TC-NLP-03", "NLP Model", "Maintenance activity detection", text, "Maintenance / High", f"{res['category']} / {res['priority']}", passed, elapsed)
        self.assertTrue(passed)

    def test_nlp_04_admin_low(self):
        t0 = time.perf_counter()
        text = "Updated shift logbook Section 4 and filed maintenance work orders."
        res = self.nlp.analyze_task(text)
        elapsed = (time.perf_counter() - t0) * 1000
        passed = (res["category"] == "Administration" and res["priority"] == "Low")
        record_test("TC-NLP-04", "NLP Model", "Low priority admin logbook update", text, "Administration / Low", f"{res['category']} / {res['priority']}", passed, elapsed)
        self.assertTrue(passed)

    def test_nlp_05_multi_task_segmentation(self):
        t0 = time.perf_counter()
        text = "Checked boiler pressure on Line 2, replaced faulty sensor on conveyor B, and initiated safety drill log."
        res = self.nlp.analyze_shift_log(text)
        elapsed = (time.perf_counter() - t0) * 1000
        count = res["tasks_detected_count"]
        passed = (count == 3)
        record_test("TC-NLP-05", "NLP Segmentation", "Split compound multi-task notes", text, "3 discrete tasks", f"{count} discrete tasks", passed, elapsed)
        self.assertEqual(count, 3)

class TestShiftSyncAPI(unittest.TestCase):
    _server_thread = None
    _httpd = None

    @classmethod
    def setUpClass(cls):
        # Verify if server is already running
        try:
            with urllib.request.urlopen(f"{API_BASE}/api/dashboard-stats", timeout=0.5) as resp:
                if resp.status == 200:
                    return
        except Exception:
            pass

        # Spawn in background daemon thread
        import socketserver
        import threading
        from server import ShiftSyncRequestHandler, PORT
        socketserver.TCPServer.allow_reuse_address = True
        cls._httpd = socketserver.TCPServer(("", PORT), ShiftSyncRequestHandler)
        cls._server_thread = threading.Thread(target=cls._httpd.serve_forever, daemon=True)
        cls._server_thread.start()
        time.sleep(1)

    @classmethod
    def tearDownClass(cls):
        if cls._httpd:
            cls._httpd.shutdown()
            cls._httpd.server_close()

    def api_get(self, path):
        req = urllib.request.Request(f"{API_BASE}{path}")
        with urllib.request.urlopen(req) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))

    def api_post(self, path, payload):
        data_bytes = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(f"{API_BASE}{path}", data=data_bytes, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))

    def test_api_01_dashboard_stats(self):
        t0 = time.perf_counter()
        status, body = self.api_get("/api/dashboard-stats")
        elapsed = (time.perf_counter() - t0) * 1000
        passed = (status == 200 and "pending_handovers" in body and "incomplete_tasks" in body)
        record_test("TC-API-01", "REST API", "Fetch Dashboard KPI telemetry", "/api/dashboard-stats", "HTTP 200 + KPI Keys", f"HTTP {status}", passed, elapsed)
        self.assertTrue(passed)

    def test_api_02_shifts_list(self):
        t0 = time.perf_counter()
        status, body = self.api_get("/api/shifts")
        elapsed = (time.perf_counter() - t0) * 1000
        passed = (status == 200 and len(body.get("shifts", [])) > 0)
        record_test("TC-API-02", "REST API", "Retrieve active and scheduled shifts", "/api/shifts", "HTTP 200 + Shifts array", f"HTTP {status} ({len(body.get('shifts', []))} shifts)", passed, elapsed)
        self.assertTrue(passed)

    def test_api_03_create_task(self):
        t0 = time.perf_counter()
        payload = {
            "task_name": "Test Automated Brake Line Caliper Inspection",
            "assigned_to": "John Doe",
            "category": "Maintenance",
            "priority": "High",
            "due_date": "Today, 21:00",
            "status": "Pending"
        }
        status, body = self.api_post("/api/tasks", payload)
        elapsed = (time.perf_counter() - t0) * 1000
        passed = (status == 201 and "task_id" in body)
        record_test("TC-API-03", "REST API", "Create new operational task", payload["task_name"], "HTTP 201 + task_id", f"HTTP {status} (ID: {body.get('task_id')})", passed, elapsed)
        self.assertTrue(passed)

    def test_api_04_toggle_task(self):
        t0 = time.perf_counter()
        status, body = self.api_post("/api/tasks/1/toggle", {})
        elapsed = (time.perf_counter() - t0) * 1000
        passed = (status == 200 and "new_status" in body)
        record_test("TC-API-04", "REST API", "Toggle task completion lifecycle", "/api/tasks/1/toggle", "HTTP 200 + new_status", f"HTTP {status} ({body.get('new_status')})", passed, elapsed)
        self.assertTrue(passed)

    def test_api_05_create_handover_report(self):
        t0 = time.perf_counter()
        payload = {
            "shift_id": 1,
            "outgoing_operator": "John Doe",
            "incoming_operator": "Michael Chang",
            "equipment_status": "Auxiliary turbine running smoothly at 1400 RPM.",
            "safety_notes": "All safety guards locked in place.",
            "additional_notes": "Shift turnover complete.",
            "tasks": [
                {"task": "Verify generator fuel reserve", "category": "Equipment Check", "priority": "High", "status": "Pending"}
            ]
        }
        status, body = self.api_post("/api/handovers", payload)
        elapsed = (time.perf_counter() - t0) * 1000
        passed = (status == 201 and "report_code" in body)
        self.created_report_code = body.get("report_code")
        record_test("TC-API-05", "REST API", "Submit end-of-shift handover report", payload["outgoing_operator"] + " -> " + payload["incoming_operator"], "HTTP 201 + report_code", f"HTTP {status} (Code: {self.created_report_code})", passed, elapsed)
        self.assertTrue(passed)

    def test_api_06_acknowledge_handover(self):
        t0 = time.perf_counter()
        code = "HO-2026-088"
        status, body = self.api_post(f"/api/handovers/{code}/acknowledge", {"user": "Michael Chang"})
        elapsed = (time.perf_counter() - t0) * 1000
        passed = (status == 200 and body.get("message") == "Handover acknowledged successfully")
        record_test("TC-API-06", "REST API", "Formal digital acknowledgment sign-off", f"/api/handovers/{code}/acknowledge", "HTTP 200 + Acknowledged", f"HTTP {status}", passed, elapsed)
        self.assertTrue(passed)

class TestShiftSyncDatabase(unittest.TestCase):
    def setUp(self):
        self.conn = database.get_connection()

    def tearDown(self):
        self.conn.close()

    def test_db_01_referential_integrity(self):
        t0 = time.perf_counter()
        cursor = self.conn.cursor()
        # Verify foreign key from handover_reports to shifts
        cursor.execute("""
        SELECT h.report_code, s.shift_name 
        FROM handover_reports h 
        JOIN shifts s ON h.shift_id = s.id 
        LIMIT 1
        """)
        row = cursor.fetchone()
        elapsed = (time.perf_counter() - t0) * 1000
        passed = (row is not None and len(row["report_code"]) > 0)
        record_test("TC-DB-01", "Database Integrity", "FK referential link (Handover -> Shift)", "FK join handover_reports & shifts", "Valid row joined", f"Joined ({row['report_code']} -> {row['shift_name']})", passed, elapsed)
        self.assertTrue(passed)

    def test_db_02_status_constraint(self):
        t0 = time.perf_counter()
        cursor = self.conn.cursor()
        # Ensure invalid role is rejected by CHECK constraint
        threw_error = False
        try:
            cursor.execute("INSERT INTO users (name, email, role, department) VALUES ('Hacker', 'hack@bad.com', 'INVALID_ROLE', 'None')")
            self.conn.commit()
        except sqlite3.IntegrityError:
            threw_error = True
        elapsed = (time.perf_counter() - t0) * 1000
        record_test("TC-DB-02", "Database Integrity", "Role check constraint enforcement", "role = 'INVALID_ROLE'", "sqlite3.IntegrityError", "IntegrityError raised (blocked)" if threw_error else "Failed to block", threw_error, elapsed)
        self.assertTrue(threw_error)

if __name__ == "__main__":
    print("=" * 80)
    print("RUNNING SHIFTSYNC AUTOMATED SYSTEM & NLP VERIFICATION SUITE")
    print("=" * 80)
    
    suite = unittest.TestSuite()
    loader = unittest.TestLoader()
    suite.addTest(loader.loadTestsFromTestCase(TestShiftSyncNLP))
    suite.addTest(loader.loadTestsFromTestCase(TestShiftSyncAPI))
    suite.addTest(loader.loadTestsFromTestCase(TestShiftSyncDatabase))

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Compile Markdown Results Table for Chapter 4
    md_output = []
    md_output.append("# ShiftSync System & NLP Verification Test Report")
    md_output.append(f"**Execution Date**: {time.strftime('%Y-%m-%d %H:%M:%S')}  ")
    md_output.append(f"**Total Test Cases Executed**: {result.testsRun}  ")
    md_output.append(f"**Passed**: {result.testsRun - len(result.failures) - len(result.errors)}  ")
    md_output.append(f"**Failed**: {len(result.failures) + len(result.errors)}  ")
    md_output.append(f"**Pass Rate**: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun) * 100:.1f}%\n")
    
    md_output.append("### Table 4.X: System Test Cases and Verification Results\n")
    md_output.append("| Test ID | Module | Description | Input / Condition | Expected Result | Actual Result | Status | Latency |")
    md_output.append("| :--- | :--- | :--- | :--- | :--- | :--- | :---: | :---: |")

    for r in test_records:
        md_output.append(f"| `{r['id']}` | **{r['module']}** | {r['description']} | `{r['input']}` | {r['expected']} | {r['actual']} | **{r['status']}** | {r['time_ms']} |")

    report_path = os.path.join(BASE_DIR, "docs", "test_results.md")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(md_output))

    print("\n" + "=" * 80)
    print(f"Test Report successfully exported for Chapter 4 to:")
    print(f"{report_path}")
    print("=" * 80)
