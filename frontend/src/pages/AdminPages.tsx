import React, { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import {
  AlertTriangle,
  BrainCircuit,
  CalendarClock,
  CheckCircle2,
  Edit,
  Plus,
  Power,
  Save,
  Settings,
  ShieldCheck,
  UserPlus,
  Users,
} from "lucide-react";
import { apiClient } from "../api/client";
import { useAuth } from "../context/AuthContext";

/* ============================================================================
   PAGE 18: USER MANAGEMENT (/admin/users)
   ============================================================================ */
export const UserManagementPage: React.FC = () => {
  const [users, setUsers] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [roleFilter, setRoleFilter] = useState("");
  const [searchQuery, setSearchQuery] = useState("");

  const loadUsers = async () => {
    setLoading(true);
    try {
      const params: Record<string, string> = {};
      if (roleFilter) params.role = roleFilter;
      if (searchQuery.trim()) params.search = searchQuery.trim();
      const res = await apiClient.get("/users/", { params });
      setUsers(res.data.results || res.data || []);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadUsers();
  }, [roleFilter]);

  const handleToggleActive = async (userId: string) => {
    await apiClient.post(`/users/${userId}/toggle-status/`, {});
    loadUsers();
  };

  return (
    <div>
      <div className="card-header" style={{ marginBottom: "1.25rem" }}>
        <div>
          <h1 style={{ fontSize: "1.4rem", fontWeight: 700 }}>
            System Administration — User Management
          </h1>
          <p style={{ fontSize: "0.85rem", color: "var(--slate-500)" }}>
            Provision accounts, assign operational roles and departments, and manage account status
          </p>
        </div>

        <Link
          to="/admin/users/new"
          className="btn btn-primary"
          data-testid="admin-new-user-link"
        >
          <UserPlus size={16} />
          <span>Provision New User Account</span>
        </Link>
      </div>

      <div className="card" style={{ marginBottom: "1.25rem" }}>
        <div className="grid-2">
          <div>
            <label className="form-label">Search Name, Email, or Employee ID</label>
            <div style={{ display: "flex", gap: "0.5rem" }}>
              <input
                type="text"
                className="form-control"
                placeholder="Search users..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
              />
              <button
                type="button"
                className="btn btn-secondary"
                onClick={loadUsers}
              >
                Search
              </button>
            </div>
          </div>

          <div>
            <label className="form-label">Filter by Role</label>
            <select
              className="form-control"
              value={roleFilter}
              onChange={(e) => setRoleFilter(e.target.value)}
            >
              <option value="">All Roles</option>
              <option value="OUTGOING_WORKER">Outgoing Worker</option>
              <option value="INCOMING_WORKER">Incoming Worker</option>
              <option value="SUPERVISOR">Supervisor</option>
              <option value="ADMIN">System Administrator</option>
            </select>
          </div>
        </div>
      </div>

      <div className="card">
        {loading ? (
          <p style={{ padding: "2rem", textAlign: "center" }}>Loading users...</p>
        ) : (
          <div className="table-wrap">
            <table className="data-table" data-testid="admin-users-table">
              <thead>
                <tr>
                  <th>Full Name</th>
                  <th>Email Address</th>
                  <th>Employee ID</th>
                  <th>Role</th>
                  <th>Department</th>
                  <th>Status</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {users.map((u) => (
                  <tr key={u.id}>
                    <td style={{ fontWeight: 600 }}>{u.full_name}</td>
                    <td className="mono" style={{ fontSize: "0.8rem" }}>
                      {u.email}
                    </td>
                    <td className="mono">{u.employee_id || "—"}</td>
                    <td>
                      <span className="badge badge-teal">{u.role_display}</span>
                    </td>
                    <td>{u.department}</td>
                    <td>
                      <span
                        className={`badge ${
                          u.is_active ? "badge-green" : "badge-red"
                        }`}
                      >
                        {u.is_active ? "Active" : "Deactivated"}
                      </span>
                    </td>
                    <td>
                      <div style={{ display: "flex", gap: "0.4rem" }}>
                        <Link
                          to={`/admin/users/${u.id}/edit`}
                          className="btn btn-secondary btn-sm"
                        >
                          <Edit size={13} />
                          <span>Edit</span>
                        </Link>
                        <button
                          type="button"
                          className={`btn btn-sm ${
                            u.is_active ? "btn-danger" : "btn-success"
                          }`}
                          onClick={() => handleToggleActive(u.id)}
                        >
                          <Power size={13} />
                          <span>{u.is_active ? "Deactivate" : "Activate"}</span>
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};

/* ============================================================================
   PAGE 19: CREATE & EDIT USER (/admin/users/new, /admin/users/:id/edit)
   ============================================================================ */
export const CreateEditUserPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { organisation } = useAuth();

  const [email, setEmail] = useState("");
  const [fullName, setFullName] = useState("");
  const [employeeId, setEmployeeId] = useState("");
  const [role, setRole] = useState("OUTGOING_WORKER");
  const [department, setDepartment] = useState(
    organisation?.departments?.[0] || "Line Maintenance"
  );
  const [phoneNumber, setPhoneNumber] = useState("");
  const [password, setPassword] = useState("");
  const [isActive, setIsActive] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (id) {
      apiClient.get(`/users/${id}/`).then((res) => {
        const u = res.data;
        setEmail(u.email);
        setFullName(u.full_name);
        setEmployeeId(u.employee_id || "");
        setRole(u.role);
        setDepartment(u.department || "Line Maintenance");
        setPhoneNumber(u.phone_number || "");
        setIsActive(Boolean(u.is_active));
      });
    }
  }, [id]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSaving(true);
    try {
      const payload: Record<string, any> = {
        email: email.trim().toLowerCase(),
        full_name: fullName.trim(),
        employee_id: employeeId.trim(),
        role,
        department: department.trim(),
        phone_number: phoneNumber.trim(),
        is_active: isActive,
      };
      if (password) {
        payload.password = password;
      }
      if (id) {
        await apiClient.patch(`/users/${id}/`, payload);
      } else {
        await apiClient.post("/users/", payload);
      }
      navigate("/admin/users");
    } catch (err: any) {
      const d = err.response?.data;
      setError(
        d?.detail ||
          d?.email?.[0] ||
          d?.password?.[0] ||
          "Failed to save user account. Verify email uniqueness and password strength."
      );
    } finally {
      setSaving(false);
    }
  };

  return (
    <div style={{ maxWidth: "680px" }}>
      <div style={{ marginBottom: "1.25rem" }}>
        <h1 style={{ fontSize: "1.4rem", fontWeight: 700 }}>
          {id ? "Edit User Account & Role" : "Create & Provision User Account"}
        </h1>
        <p style={{ fontSize: "0.85rem", color: "var(--slate-500)" }}>
          Assign role-based permissions and department scope within {organisation?.name}
        </p>
      </div>

      {error && (
        <div className="alert alert-error" role="alert">
          <AlertTriangle size={18} />
          <span>{error}</span>
        </div>
      )}

      <div className="card">
        <form onSubmit={handleSubmit}>
          <div className="grid-2">
            <div className="form-group">
              <label htmlFor="u-fullname" className="form-label">
                Full Name
              </label>
              <input
                id="u-fullname"
                type="text"
                className="form-control"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                required
                data-testid="user-fullname-input"
              />
            </div>

            <div className="form-group">
              <label htmlFor="u-email" className="form-label">
                Work Email Address
              </label>
              <input
                id="u-email"
                type="email"
                className="form-control"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                data-testid="user-email-input"
              />
            </div>
          </div>

          <div className="grid-2">
            <div className="form-group">
              <label htmlFor="u-role" className="form-label">
                Assigned System Role
              </label>
              <select
                id="u-role"
                className="form-control"
                value={role}
                onChange={(e) => setRole(e.target.value)}
                data-testid="user-role-select"
              >
                <option value="OUTGOING_WORKER">Outgoing Worker</option>
                <option value="INCOMING_WORKER">Incoming Worker</option>
                <option value="SUPERVISOR">Supervisor</option>
                <option value="ADMIN">System Administrator</option>
              </select>
            </div>

            <div className="form-group">
              <label htmlFor="u-dept" className="form-label">
                Department / Unit
              </label>
              <input
                id="u-dept"
                type="text"
                className="form-control"
                value={department}
                onChange={(e) => setDepartment(e.target.value)}
                required
                data-testid="user-department-input"
              />
            </div>
          </div>

          <div className="grid-2">
            <div className="form-group">
              <label htmlFor="u-empid" className="form-label">
                Employee ID
              </label>
              <input
                id="u-empid"
                type="text"
                className="form-control mono"
                value={employeeId}
                onChange={(e) => setEmployeeId(e.target.value)}
              />
            </div>

            <div className="form-group">
              <label htmlFor="u-pw" className="form-label">
                {id ? "New Password (leave blank to keep existing)" : "Initial Password (min 8 chars)"}
              </label>
              <input
                id="u-pw"
                type="password"
                className="form-control"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required={!id}
                minLength={8}
                data-testid="user-password-input"
              />
            </div>
          </div>

          <div className="form-group" style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
            <input
              id="u-active"
              type="checkbox"
              checked={isActive}
              onChange={(e) => setIsActive(e.target.checked)}
            />
            <label htmlFor="u-active" style={{ fontSize: "0.85rem", fontWeight: 600 }}>
              Account Active (Authorised to Sign In)
            </label>
          </div>

          <div style={{ display: "flex", gap: "0.65rem" }}>
            <button
              type="submit"
              className="btn btn-primary"
              disabled={saving}
              data-testid="save-user-submit-btn"
            >
              <Save size={16} />
              <span>{saving ? "Saving..." : id ? "Update User Account" : "Create User Account"}</span>
            </button>
            <Link to="/admin/users" className="btn btn-secondary">
              Cancel
            </Link>
          </div>
        </form>
      </div>
    </div>
  );
};

/* ============================================================================
   PAGE 20: CREATE & EDIT SHIFTS (/admin/shifts/new, /admin/shifts/:id/edit)
   ============================================================================ */
export const CreateEditShiftPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  const [colleagues, setColleagues] = useState<any[]>([]);
  const [name, setName] = useState("");
  const [department, setDepartment] = useState("Line Maintenance");
  const [shiftDate, setShiftDate] = useState(
    new Date().toISOString().slice(0, 10)
  );
  const [startTime, setStartTime] = useState("06:00");
  const [endTime, setEndTime] = useState("14:00");
  const [outgoingWorker, setOutgoingWorker] = useState("");
  const [incomingWorker, setIncomingWorker] = useState("");
  const [supervisor, setSupervisor] = useState("");
  const [status, setStatus] = useState("ACTIVE");
  const [notes, setNotes] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    apiClient.get("/users/colleagues/").then((res) => {
      const list = res.data || [];
      setColleagues(list);
      if (!id && list.length >= 2) {
        const out = list.find((u: any) => u.role === "OUTGOING_WORKER") || list[0];
        const inc =
          list.find((u: any) => u.role === "INCOMING_WORKER" && u.id !== out.id) ||
          list.find((u: any) => u.id !== out.id);
        const sup = list.find((u: any) => u.role === "SUPERVISOR");
        if (out) setOutgoingWorker(out.id);
        if (inc) setIncomingWorker(inc.id);
        if (sup) setSupervisor(sup.id);
      }
    });

    if (id) {
      apiClient.get(`/shifts/${id}/`).then((res) => {
        const s = res.data;
        setName(s.name);
        setDepartment(s.department);
        setShiftDate(s.shift_date);
        setStartTime(s.start_time.slice(0, 5));
        setEndTime(s.end_time.slice(0, 5));
        setOutgoingWorker(s.outgoing_worker);
        setIncomingWorker(s.incoming_worker);
        setSupervisor(s.supervisor || "");
        setStatus(s.status);
        setNotes(s.notes || "");
      });
    }
  }, [id]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSaving(true);
    try {
      const payload = {
        name: name.trim(),
        department: department.trim(),
        shift_date: shiftDate,
        start_time: startTime,
        end_time: endTime,
        outgoing_worker: outgoingWorker,
        incoming_worker: incomingWorker,
        supervisor: supervisor || null,
        status,
        notes,
      };
      if (id) {
        await apiClient.patch(`/shifts/${id}/`, payload);
      } else {
        await apiClient.post("/shifts/", payload);
      }
      navigate("/shifts");
    } catch (err: any) {
      const d = err.response?.data;
      setError(
        d?.detail ||
          d?.incoming_worker?.[0] ||
          d?.outgoing_worker?.[0] ||
          "Failed to save shift assignment."
      );
    } finally {
      setSaving(false);
    }
  };

  return (
    <div style={{ maxWidth: "720px" }}>
      <div style={{ marginBottom: "1.25rem" }}>
        <h1 style={{ fontSize: "1.4rem", fontWeight: 700 }}>
          {id ? "Edit Shift & Worker Assignment" : "Create & Assign Operational Shift"}
        </h1>
        <p style={{ fontSize: "0.85rem", color: "var(--slate-500)" }}>
          Configure shift date, time window, and outgoing/incoming worker responsibility pair
        </p>
      </div>

      {error && (
        <div className="alert alert-error" role="alert">
          <AlertTriangle size={18} />
          <span>{error}</span>
        </div>
      )}

      <div className="card">
        <form onSubmit={handleSubmit}>
          <div className="grid-2">
            <div className="form-group">
              <label htmlFor="s-name" className="form-label">
                Shift Name / Title
              </label>
              <input
                id="s-name"
                type="text"
                className="form-control"
                placeholder="e.g., Morning Line Maintenance Shift Alpha"
                value={name}
                onChange={(e) => setName(e.target.value)}
                required
                data-testid="shift-name-input"
              />
            </div>

            <div className="form-group">
              <label htmlFor="s-dept" className="form-label">
                Department
              </label>
              <input
                id="s-dept"
                type="text"
                className="form-control"
                value={department}
                onChange={(e) => setDepartment(e.target.value)}
                required
              />
            </div>
          </div>

          <div className="grid-3">
            <div className="form-group">
              <label htmlFor="s-date" className="form-label">
                Shift Date
              </label>
              <input
                id="s-date"
                type="date"
                className="form-control"
                value={shiftDate}
                onChange={(e) => setShiftDate(e.target.value)}
                required
                data-testid="shift-date-input"
              />
            </div>

            <div className="form-group">
              <label htmlFor="s-start" className="form-label">
                Start Time
              </label>
              <input
                id="s-start"
                type="time"
                className="form-control"
                value={startTime}
                onChange={(e) => setStartTime(e.target.value)}
                required
              />
            </div>

            <div className="form-group">
              <label htmlFor="s-end" className="form-label">
                End Time
              </label>
              <input
                id="s-end"
                type="time"
                className="form-control"
                value={endTime}
                onChange={(e) => setEndTime(e.target.value)}
                required
              />
            </div>
          </div>

          <div className="grid-2">
            <div className="form-group">
              <label htmlFor="s-out" className="form-label">
                Assigned Outgoing Worker
              </label>
              <select
                id="s-out"
                className="form-control"
                value={outgoingWorker}
                onChange={(e) => setOutgoingWorker(e.target.value)}
                required
                data-testid="shift-outgoing-select"
              >
                <option value="">-- Select Outgoing Worker --</option>
                {colleagues.map((u) => (
                  <option key={u.id} value={u.id}>
                    {u.full_name} ({u.email} • {u.role_display})
                  </option>
                ))}
              </select>
            </div>

            <div className="form-group">
              <label htmlFor="s-inc" className="form-label">
                Assigned Incoming Worker
              </label>
              <select
                id="s-inc"
                className="form-control"
                value={incomingWorker}
                onChange={(e) => setIncomingWorker(e.target.value)}
                required
                data-testid="shift-incoming-select"
              >
                <option value="">-- Select Incoming Worker --</option>
                {colleagues.map((u) => (
                  <option key={u.id} value={u.id}>
                    {u.full_name} ({u.email} • {u.role_display})
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div className="grid-2">
            <div className="form-group">
              <label htmlFor="s-sup" className="form-label">
                Shift Supervisor (Optional)
              </label>
              <select
                id="s-sup"
                className="form-control"
                value={supervisor}
                onChange={(e) => setSupervisor(e.target.value)}
              >
                <option value="">-- None --</option>
                {colleagues
                  .filter((u) => u.role === "SUPERVISOR" || u.role === "ADMIN")
                  .map((u) => (
                    <option key={u.id} value={u.id}>
                      {u.full_name} ({u.role_display})
                    </option>
                  ))}
              </select>
            </div>

            <div className="form-group">
              <label htmlFor="s-status" className="form-label">
                Shift Status
              </label>
              <select
                id="s-status"
                className="form-control"
                value={status}
                onChange={(e) => setStatus(e.target.value)}
              >
                <option value="ACTIVE">Active</option>
                <option value="SCHEDULED">Scheduled</option>
                <option value="COMPLETED">Completed</option>
                <option value="CANCELLED">Cancelled</option>
              </select>
            </div>
          </div>

          <div className="form-group">
            <label htmlFor="s-notes" className="form-label">
              Shift Operational Notes
            </label>
            <textarea
              id="s-notes"
              className="form-control"
              rows={2}
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
            />
          </div>

          <div style={{ display: "flex", gap: "0.65rem" }}>
            <button
              type="submit"
              className="btn btn-primary"
              disabled={saving}
              data-testid="save-shift-submit-btn"
            >
              <Save size={16} />
              <span>{saving ? "Saving..." : id ? "Update Shift" : "Create & Assign Shift"}</span>
            </button>
            <Link to="/shifts" className="btn btn-secondary">
              Cancel
            </Link>
          </div>
        </form>
      </div>
    </div>
  );
};

/* ============================================================================
   PAGE 21: BASIC SYSTEM CONFIGURATION & AUDIT LOGS (/admin/configuration)
   ============================================================================ */
export const SystemConfigurationPage: React.FC = () => {
  const { refreshProfile } = useAuth();
  const [orgConfig, setOrgConfig] = useState<any | null>(null);
  const [nlpStatus, setNlpStatus] = useState<any | null>(null);
  const [auditLogs, setAuditLogs] = useState<any[]>([]);
  const [categoriesStr, setCategoriesStr] = useState("");
  const [departmentsStr, setDepartmentsStr] = useState("");
  const [lowConfThreshold, setLowConfThreshold] = useState(60.0);
  const [requireAckNotes, setRequireAckNotes] = useState(false);
  const [nlpEnabled, setNlpEnabled] = useState(true);
  const [msg, setMsg] = useState<string | null>(null);

  const loadConfig = async () => {
    const [orgRes, nlpRes, auditRes] = await Promise.all([
      apiClient.get("/organisations/current/"),
      apiClient.get("/nlp/status/"),
      apiClient.get("/organisations/audit-logs/"),
    ]);
    const o = orgRes.data;
    setOrgConfig(o);
    setCategoriesStr((o.task_categories || []).join(", "));
    setDepartmentsStr((o.departments || []).join(", "));
    setLowConfThreshold(o.low_confidence_threshold ?? 60.0);
    setRequireAckNotes(Boolean(o.require_acknowledgment_notes));
    setNlpEnabled(Boolean(o.nlp_enabled));
    setNlpStatus(nlpRes.data);
    setAuditLogs(auditRes.data.results || auditRes.data || []);
  };

  useEffect(() => {
    loadConfig();
  }, []);

  const handleSaveConfig = async (e: React.FormEvent) => {
    e.preventDefault();
    setMsg(null);
    const categories = categoriesStr
      .split(",")
      .map((s) => s.trim())
      .filter(Boolean);
    const departments = departmentsStr
      .split(",")
      .map((s) => s.trim())
      .filter(Boolean);
    await apiClient.patch("/organisations/current/", {
      task_categories: categories,
      departments,
      low_confidence_threshold: Number(lowConfThreshold),
      require_acknowledgment_notes: requireAckNotes,
      nlp_enabled: nlpEnabled,
    });
    await refreshProfile();
    await loadConfig();
    setMsg("System configuration updated and persisted to PostgreSQL.");
  };

  return (
    <div>
      <div style={{ marginBottom: "1.25rem" }}>
        <h1 style={{ fontSize: "1.4rem", fontWeight: 700 }}>
          System Configuration, NLP Model Status & Security Audit Trail
        </h1>
        <p style={{ fontSize: "0.85rem", color: "var(--slate-500)" }}>
          Configure task categories, NLP confidence thresholds, handover policies, and inspect immutable system audit events
        </p>
      </div>

      {msg && (
        <div className="alert alert-success">
          <CheckCircle2 size={16} />
          <span>{msg}</span>
        </div>
      )}

      <div className="grid-2" style={{ marginBottom: "1.25rem" }}>
        <div className="card">
          <h2 className="card-title" style={{ marginBottom: "0.85rem" }}>
            Organisation & Handover Workflow Policy
          </h2>
          <form onSubmit={handleSaveConfig}>
            <div className="form-group">
              <label className="form-label">
                Configurable Task Categories (Comma-Separated)
              </label>
              <input
                type="text"
                className="form-control"
                value={categoriesStr}
                onChange={(e) => setCategoriesStr(e.target.value)}
              />
            </div>

            <div className="form-group">
              <label className="form-label">
                Configured Departments (Comma-Separated)
              </label>
              <input
                type="text"
                className="form-control"
                value={departmentsStr}
                onChange={(e) => setDepartmentsStr(e.target.value)}
              />
            </div>

            <div className="form-group">
              <label className="form-label">
                NLP Low-Confidence Warning Threshold (%)
              </label>
              <input
                type="number"
                className="form-control"
                min={10}
                max={99}
                step={1}
                value={lowConfThreshold}
                onChange={(e) => setLowConfThreshold(Number(e.target.value))}
              />
            </div>

            <div className="form-group" style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
              <input
                id="cfg-nlp-enabled"
                type="checkbox"
                checked={nlpEnabled}
                onChange={(e) => setNlpEnabled(e.target.checked)}
              />
              <label htmlFor="cfg-nlp-enabled" style={{ fontSize: "0.85rem", fontWeight: 600 }}>
                Enable Automated NLP Task Categorisation & Priority Detection
              </label>
            </div>

            <div className="form-group" style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
              <input
                id="cfg-req-notes"
                type="checkbox"
                checked={requireAckNotes}
                onChange={(e) => setRequireAckNotes(e.target.checked)}
              />
              <label htmlFor="cfg-req-notes" style={{ fontSize: "0.85rem", fontWeight: 600 }}>
                Require Mandatory Sign-Off Notes on Incoming Handover Acknowledgment
              </label>
            </div>

            <button type="submit" className="btn btn-primary">
              <Save size={16} />
              <span>Save System Configuration</span>
            </button>
          </form>
        </div>

        <div className="card">
          <h2 className="card-title" style={{ marginBottom: "0.85rem" }}>
            NLP Classifier Engine Status & Test Metrics
          </h2>
          {nlpStatus ? (
            <div style={{ fontSize: "0.86rem", display: "grid", gap: "0.55rem" }}>
              <div>
                <strong>Active Inference Provider:</strong>{" "}
                <span className="badge badge-teal">{nlpStatus.active_provider}</span>
              </div>
              <div>
                <strong>Hugging Face Transformer (`prajjwal1/bert-tiny` Fine-Tuned):</strong>{" "}
                <span className="badge badge-green">
                  {nlpStatus.huggingface_transformer_available ? "Online & Loaded" : "Unavailable"}
                </span>
              </div>
              <div>
                <strong>Calibrated Scikit-Learn Fallback Pipeline:</strong>{" "}
                <span className="badge badge-green">
                  {nlpStatus.sklearn_baseline_available ? "Ready" : "Unavailable"}
                </span>
              </div>
              {nlpStatus.evaluation_metrics?.huggingface_transformer && (
                <div
                  style={{
                    marginTop: "0.5rem",
                    padding: "0.75rem",
                    borderRadius: "8px",
                    backgroundColor: "var(--slate-50)",
                    border: "1px solid var(--slate-200)",
                  }}
                >
                  <div style={{ fontWeight: 700, marginBottom: "0.35rem" }}>
                    Unseen Test Partition Benchmark (70/15/15 Split, 0% Leakage):
                  </div>
                  <div>
                    • <strong>Transformer Category Accuracy:</strong>{" "}
                    {(
                      nlpStatus.evaluation_metrics.huggingface_transformer.category
                        .test_accuracy * 100
                    ).toFixed(2)}
                    %
                  </div>
                  <div>
                    • <strong>Transformer Priority Accuracy:</strong>{" "}
                    {(
                      nlpStatus.evaluation_metrics.huggingface_transformer.priority
                        .test_accuracy * 100
                    ).toFixed(2)}
                    %
                  </div>
                  <div>
                    • <strong>Dataset Size:</strong>{" "}
                    {nlpStatus.evaluation_metrics.dataset_records} deduplicated records
                  </div>
                </div>
              )}
            </div>
          ) : (
            <p>Loading NLP status...</p>
          )}
        </div>
      </div>

      <div className="card">
        <h2 className="card-title" style={{ marginBottom: "0.85rem" }}>
          System-Level Immutable Audit Trail ({auditLogs.length} Recent Events)
        </h2>
        <div className="table-wrap">
          <table className="data-table">
            <thead>
              <tr>
                <th>Timestamp (UTC)</th>
                <th>Action</th>
                <th>Actor</th>
                <th>Target</th>
                <th>Event Summary</th>
              </tr>
            </thead>
            <tbody>
              {auditLogs.map((ev) => (
                <tr key={ev.id}>
                  <td className="mono" style={{ fontSize: "0.76rem" }}>
                    {new Date(ev.created_at).toLocaleString()}
                  </td>
                  <td>
                    <span className="badge badge-slate">{ev.action}</span>
                  </td>
                  <td>
                    {ev.actor_name} {ev.actor_role ? `(${ev.actor_role})` : ""}
                  </td>
                  <td className="mono" style={{ fontSize: "0.75rem" }}>
                    {ev.target_type}
                  </td>
                  <td>{ev.summary}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
