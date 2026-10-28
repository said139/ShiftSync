import React, { useEffect, useState } from "react";
import { Link, useNavigate, useParams, useSearchParams } from "react-router-dom";
import {
  AlertTriangle,
  BrainCircuit,
  CalendarClock,
  CheckCircle2,
  ClipboardCheck,
  Eye,
  FileCheck2,
  FileEdit,
  FilePlus2,
  History,
  Plus,
  Save,
  Send,
  ShieldAlert,
  Sparkles,
  Trash2,
} from "lucide-react";
import { apiClient } from "../api/client";
import { useAuth } from "../context/AuthContext";
import {
  EquipmentStatusBadge,
  HandoverStatusBadge,
  PriorityBadge,
  TaskStatusBadge,
} from "../components/Badges";

/* ============================================================================
   PAGE 9: SHIFT MANAGEMENT (/shifts)
   ============================================================================ */
export const ShiftManagementPage: React.FC = () => {
  const { user } = useAuth();
  const [shifts, setShifts] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [myShiftsOnly, setMyShiftsOnly] = useState(
    user?.role === "OUTGOING_WORKER" || user?.role === "INCOMING_WORKER"
  );
  const [statusFilter, setStatusFilter] = useState("");

  const loadShifts = async () => {
    setLoading(true);
    try {
      const params: Record<string, string> = {};
      if (myShiftsOnly) params.my_shifts = "true";
      if (statusFilter) params.status = statusFilter;
      const res = await apiClient.get("/shifts/", { params });
      setShifts(res.data.results || res.data || []);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadShifts();
  }, [myShiftsOnly, statusFilter]);

  return (
    <div>
      <div className="card-header" style={{ marginBottom: "1.25rem" }}>
        <div>
          <h1 style={{ fontSize: "1.4rem", fontWeight: 700 }}>Shift Management</h1>
          <p style={{ fontSize: "0.85rem", color: "var(--slate-500)" }}>
            View active, scheduled, and completed shifts and worker handover assignments
          </p>
        </div>

        <div style={{ display: "flex", gap: "0.6rem", flexWrap: "wrap" }}>
          <button
            type="button"
            className={`btn btn-sm ${myShiftsOnly ? "btn-primary" : "btn-secondary"}`}
            onClick={() => setMyShiftsOnly(!myShiftsOnly)}
          >
            {myShiftsOnly ? "Showing My Assigned Shifts" : "Showing All Organisation Shifts"}
          </button>
          <select
            className="form-control"
            style={{ width: "auto", padding: "0.35rem 0.65rem", fontSize: "0.82rem" }}
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
          >
            <option value="">All Shift Statuses</option>
            <option value="ACTIVE">Active</option>
            <option value="SCHEDULED">Scheduled</option>
            <option value="COMPLETED">Completed</option>
          </select>
          {user?.role === "ADMIN" && (
            <Link to="/admin/shifts/new" className="btn btn-primary btn-sm">
              <Plus size={15} />
              <span>Create & Assign Shift</span>
            </Link>
          )}
        </div>
      </div>

      <div className="card">
        {loading ? (
          <p style={{ padding: "2rem", textAlign: "center" }}>Loading shifts...</p>
        ) : shifts.length === 0 ? (
          <p style={{ padding: "2rem", textAlign: "center", color: "var(--slate-500)" }}>
            No shifts found for the selected view.
          </p>
        ) : (
          <div className="table-wrap">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Shift Name</th>
                  <th>Department</th>
                  <th>Date & Time Window</th>
                  <th>Outgoing Worker</th>
                  <th>Incoming Worker</th>
                  <th>Supervisor</th>
                  <th>Status</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {shifts.map((s) => (
                  <tr key={s.id}>
                    <td style={{ fontWeight: 600 }}>{s.name}</td>
                    <td>{s.department}</td>
                    <td className="mono" style={{ fontSize: "0.8rem" }}>
                      {s.shift_date} ({s.start_time.slice(0, 5)} – {s.end_time.slice(0, 5)})
                    </td>
                    <td>{s.outgoing_worker_name}</td>
                    <td>{s.incoming_worker_name}</td>
                    <td>{s.supervisor_name || "—"}</td>
                    <td>
                      <span
                        className={`badge ${
                          s.status === "ACTIVE"
                            ? "badge-green"
                            : s.status === "SCHEDULED"
                            ? "badge-teal"
                            : "badge-slate"
                        }`}
                      >
                        {s.status_display}
                      </span>
                    </td>
                    <td>
                      <div style={{ display: "flex", gap: "0.4rem" }}>
                        {(user?.role === "OUTGOING_WORKER" || user?.role === "ADMIN") && (
                          <Link
                            to={`/handovers/create?shift=${s.id}`}
                            className="btn btn-primary btn-sm"
                          >
                            Prepare Handover
                          </Link>
                        )}
                        {user?.role === "ADMIN" && (
                          <Link
                            to={`/admin/shifts/${s.id}/edit`}
                            className="btn btn-secondary btn-sm"
                          >
                            Edit
                          </Link>
                        )}
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
   PAGE 10: CREATE & EDIT HANDOVER REPORT (/handovers/create, /handovers/:id/edit)
   ============================================================================ */
interface DraftTaskItem {
  id?: string;
  description: string;
  status: string;
  category: string;
  priority: string;
  model_suggested_category: string;
  model_suggested_priority: string;
  category_confidence: number | null;
  priority_confidence: number | null;
  confidence_score: number | null;
  nlp_provider_used: string;
  confirmed_category: string;
  confirmed_priority: string;
  due_date: string;
  contextual_notes: string;
  is_low_confidence?: boolean;
  nlp_warning?: string | null;
}

export const CreateEditHandoverPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const [searchParams] = useSearchParams();
  const preselectedShiftId = searchParams.get("shift") || "";
  const { user, organisation } = useAuth();
  const navigate = useNavigate();

  const [shifts, setShifts] = useState<any[]>([]);
  const [colleagues, setColleagues] = useState<any[]>([]);
  const [selectedShiftId, setSelectedShiftId] = useState<string>(preselectedShiftId);
  const [incomingWorkerId, setIncomingWorkerId] = useState<string>("");
  const [equipmentStatus, setEquipmentStatus] = useState<string>("OPERATIONAL");
  const [equipmentDetails, setEquipmentDetails] = useState<string>("");
  const [safetyIssues, setSafetyIssues] = useState<string>("");
  const [hasSafetyIncident, setHasSafetyIncident] = useState<boolean>(false);
  const [additionalNotes, setAdditionalNotes] = useState<string>("");
  const [reportCode, setReportCode] = useState<string>("");
  const [reportStatus, setReportStatus] = useState<string>("DRAFT");

  const [tasks, setTasks] = useState<DraftTaskItem[]>([]);

  // New Task Entry Form State
  const [taskDesc, setTaskDesc] = useState<string>("");
  const [taskStatus, setTaskStatus] = useState<string>("Pending");
  const [taskCategory, setTaskCategory] = useState<string>("Operations");
  const [taskPriority, setTaskPriority] = useState<string>("Medium");
  const [suggestedCat, setSuggestedCat] = useState<string>("");
  const [suggestedPrio, setSuggestedPrio] = useState<string>("");
  const [catConf, setCatConf] = useState<number | null>(null);
  const [prioConf, setPrioConf] = useState<number | null>(null);
  const [confScore, setConfScore] = useState<number | null>(null);
  const [nlpProvider, setNlpProvider] = useState<string>("");
  const [isLowConf, setIsLowConf] = useState<boolean>(false);
  const [nlpWarning, setNlpWarning] = useState<string | null>(null);
  const [nlpRunning, setNlpRunning] = useState<boolean>(false);
  const [taskDueDate, setTaskDueDate] = useState<string>("");
  const [taskNotes, setTaskNotes] = useState<string>("");

  const [showReviewStep, setShowReviewStep] = useState<boolean>(false);
  const [saving, setSaving] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  const categories = organisation?.task_categories || [
    "Maintenance",
    "Safety & Compliance",
    "Equipment Check",
    "Operations",
    "Inventory",
    "Customer Service",
    "Administration",
    "Other",
  ];
  const priorities = organisation?.priority_levels || [
    "Low",
    "Medium",
    "High",
    "Critical",
  ];

  useEffect(() => {
    const loadInitial = async () => {
      try {
        const [shiftsRes, usersRes] = await Promise.all([
          apiClient.get("/shifts/"),
          apiClient.get("/users/colleagues/"),
        ]);
        const shiftList = shiftsRes.data.results || shiftsRes.data || [];
        const userList = usersRes.data || [];
        setShifts(shiftList);
        setColleagues(userList);

        if (id) {
          const repRes = await apiClient.get(`/handovers/${id}/`);
          const rep = repRes.data;
          setReportCode(rep.report_code);
          setReportStatus(rep.status);
          setSelectedShiftId(rep.shift);
          setIncomingWorkerId(rep.designated_incoming_worker);
          setEquipmentStatus(rep.equipment_status);
          setEquipmentDetails(rep.equipment_details || "");
          setSafetyIssues(rep.safety_issues || "");
          setHasSafetyIncident(Boolean(rep.has_safety_incident));
          setAdditionalNotes(rep.additional_notes || "");
          setTasks(
            (rep.tasks || []).map((t: any) => ({
              id: t.id,
              description: t.description,
              status: t.status,
              category: t.confirmed_category || t.category,
              priority: t.confirmed_priority || t.priority,
              model_suggested_category: t.model_suggested_category || "",
              model_suggested_priority: t.model_suggested_priority || "",
              category_confidence: t.category_confidence,
              priority_confidence: t.priority_confidence,
              confidence_score: t.confidence_score,
              nlp_provider_used: t.nlp_provider_used || "",
              confirmed_category: t.confirmed_category || t.category,
              confirmed_priority: t.confirmed_priority || t.priority,
              due_date: t.due_date ? t.due_date.slice(0, 16) : "",
              contextual_notes: t.contextual_notes || "",
            }))
          );
        } else if (shiftList.length > 0) {
          const initialShift =
            shiftList.find((s: any) => s.id === preselectedShiftId) ||
            shiftList.find((s: any) => s.outgoing_worker === user?.id && s.status === "ACTIVE") ||
            shiftList.find((s: any) => s.outgoing_worker === user?.id) ||
            shiftList[0];
          if (initialShift) {
            setSelectedShiftId(initialShift.id);
            setIncomingWorkerId(initialShift.incoming_worker);
          }
        }
      } catch (err: any) {
        setError("Failed to load shift and colleague configuration.");
      }
    };
    loadInitial();
  }, [id]);

  const selectedShift = shifts.find((s) => s.id === selectedShiftId);

  const handleShiftChange = (newShiftId: string) => {
    setSelectedShiftId(newShiftId);
    const found = shifts.find((s) => s.id === newShiftId);
    if (found && found.incoming_worker) {
      setIncomingWorkerId(found.incoming_worker);
    }
  };

  // Step 3: Run NLP Categorisation & Priority Detection
  const handleRunNLP = async () => {
    if (nlpRunning) return;
    if (!taskDesc.trim() || taskDesc.trim().length < 3) {
      setNlpWarning("Please enter a task description (at least 3 characters) to run NLP analysis.");
      return;
    }
    setNlpRunning(true);
    setNlpWarning(null);
    try {
      const res = await apiClient.post("/nlp/predict/", {
        description: taskDesc.trim(),
      });
      const d = res.data;
      setSuggestedCat(d.category);
      setSuggestedPrio(d.priority);
      setTaskCategory(d.category);
      setTaskPriority(d.priority);
      if (d.suggested_status) {
        setTaskStatus(d.suggested_status);
      }
      setCatConf(d.category_confidence);
      setPrioConf(d.priority_confidence);
      setConfScore(d.confidence_score);
      setNlpProvider(d.provider);
      setIsLowConf(Boolean(d.is_low_confidence));
      setNlpWarning(d.warning || null);
    } catch (err: any) {
      setNlpWarning(
        err.response?.data?.detail ||
          "NLP service unavailable. Please select the task category and priority manually."
      );
    } finally {
      setNlpRunning(false);
    }
  };

  const handleAddTaskToReport = () => {
    setError(null);
    if (taskDesc.trim().length < 5) {
      setError("Task description must be at least 5 characters long.");
      return;
    }
    const newTask: DraftTaskItem = {
      description: taskDesc.trim(),
      status: taskStatus,
      category: taskCategory,
      priority: taskPriority,
      model_suggested_category: suggestedCat,
      model_suggested_priority: suggestedPrio,
      category_confidence: catConf,
      priority_confidence: prioConf,
      confidence_score: confScore,
      nlp_provider_used: nlpProvider,
      confirmed_category: taskCategory,
      confirmed_priority: taskPriority,
      due_date: taskDueDate,
      contextual_notes: taskNotes.trim(),
      is_low_confidence: isLowConf,
      nlp_warning: nlpWarning,
    };
    setTasks([...tasks, newTask]);
    // Reset task entry fields
    setTaskDesc("");
    setTaskStatus("Pending");
    setSuggestedCat("");
    setSuggestedPrio("");
    setCatConf(null);
    setPrioConf(null);
    setConfScore(null);
    setNlpProvider("");
    setIsLowConf(false);
    setNlpWarning(null);
    setTaskDueDate("");
    setTaskNotes("");
  };

  const handleUpdateQueuedTask = (
    idx: number,
    field: "confirmed_category" | "confirmed_priority" | "status",
    value: string
  ) => {
    const updated = [...tasks];
    updated[idx] = {
      ...updated[idx],
      [field]: value,
      category:
        field === "confirmed_category" ? value : updated[idx].confirmed_category,
      priority:
        field === "confirmed_priority" ? value : updated[idx].confirmed_priority,
    };
    setTasks(updated);
  };

  const handleRemoveTask = (idx: number) => {
    setTasks(tasks.filter((_, i) => i !== idx));
  };

  const buildPayload = () => ({
    shift: selectedShiftId,
    designated_incoming_worker: incomingWorkerId,
    equipment_status: equipmentStatus,
    equipment_details: equipmentDetails,
    safety_issues: safetyIssues,
    has_safety_incident: hasSafetyIncident || Boolean(safetyIssues.trim()),
    additional_notes: additionalNotes,
    tasks_input: tasks.map((t) => ({
      id: t.id || undefined,
      description: t.description,
      status: t.status,
      category: t.confirmed_category,
      priority: t.confirmed_priority,
      model_suggested_category: t.model_suggested_category,
      model_suggested_priority: t.model_suggested_priority,
      category_confidence: t.category_confidence,
      priority_confidence: t.priority_confidence,
      confidence_score: t.confidence_score,
      nlp_provider_used: t.nlp_provider_used,
      confirmed_category: t.confirmed_category,
      confirmed_priority: t.confirmed_priority,
      due_date: t.due_date ? new Date(t.due_date).toISOString() : null,
      contextual_notes: t.contextual_notes,
    })),
  });

  // Step 4: Save Draft in PostgreSQL
  const handleSaveDraft = async () => {
    setError(null);
    setSuccessMsg(null);
    if (!selectedShiftId || !incomingWorkerId) {
      setError("Please select both a shift and a designated incoming worker.");
      return;
    }
    setSaving(true);
    try {
      const payload = buildPayload();
      let res;
      if (id) {
        res = await apiClient.patch(`/handovers/${id}/`, payload);
        setSuccessMsg(`Draft ${res.data.report_code} saved in PostgreSQL.`);
      } else {
        res = await apiClient.post("/handovers/", payload);
        setSuccessMsg(`Draft ${res.data.report_code} created and persisted.`);
        navigate(`/handovers/${res.data.id}/edit`, { replace: true });
      }
    } catch (err: any) {
      const d = err.response?.data;
      setError(
        d?.detail ||
          d?.designated_incoming_worker?.[0] ||
          d?.shift?.[0] ||
          "Failed to save handover draft."
      );
    } finally {
      setSaving(false);
    }
  };

  // Step 5: Submit Handover Formally
  const handleFormalSubmit = async () => {
    setError(null);
    if (tasks.length === 0) {
      setError("Please add at least one shift task before submitting the handover report.");
      return;
    }
    setSaving(true);
    try {
      const payload = buildPayload();
      let targetId = id;
      if (!targetId) {
        const draftRes = await apiClient.post("/handovers/", payload);
        targetId = draftRes.data.id;
      } else {
        await apiClient.patch(`/handovers/${targetId}/`, payload);
      }
      const subRes = await apiClient.post(`/handovers/${targetId}/submit/`, {});
      navigate(`/handovers/${subRes.data.id}`);
    } catch (err: any) {
      const d = err.response?.data;
      setError(
        d?.detail ||
          d?.designated_incoming_worker?.[0] ||
          "Failed to submit handover report."
      );
    } finally {
      setSaving(false);
    }
  };

  if (reportStatus !== "DRAFT") {
    return (
      <div className="card">
        <div className="alert alert-warning">
          <AlertTriangle size={18} />
          <span>
            Handover report <strong>{reportCode}</strong> has already been submitted and is locked against ordinary editing.
          </span>
        </div>
        <Link to={`/handovers/${id}`} className="btn btn-primary">
          View Submitted Report & Amendment Options
        </Link>
      </div>
    );
  }

  return (
    <div>
      <div className="card-header" style={{ marginBottom: "1.25rem" }}>
        <div>
          <h1 style={{ fontSize: "1.4rem", fontWeight: 700 }}>
            {id ? `Edit Handover Draft (${reportCode})` : "Create Shift Handover Report"}
          </h1>
          <p style={{ fontSize: "0.85rem", color: "var(--slate-500)" }}>
            Record shift tasks with NLP categorisation & priority detection, save drafts to PostgreSQL, and submit formally
          </p>
        </div>
        <div style={{ display: "flex", gap: "0.6rem" }}>
          <button
            type="button"
            className="btn btn-secondary"
            onClick={handleSaveDraft}
            disabled={saving}
            data-testid="save-draft-btn"
          >
            <Save size={16} />
            <span>{saving ? "Saving..." : "Save Draft"}</span>
          </button>
          <button
            type="button"
            className="btn btn-primary"
            onClick={() => {
              if (tasks.length === 0) {
                setError("Please record at least one task before proceeding to review & submission.");
                return;
              }
              setError(null);
              setShowReviewStep(true);
            }}
            data-testid="open-review-submit-btn"
          >
            <Eye size={16} />
            <span>Review & Submit Handover ({tasks.length})</span>
          </button>
        </div>
      </div>

      {error && (
        <div className="alert alert-error" role="alert" data-testid="handover-form-error">
          <AlertTriangle size={18} />
          <span>{error}</span>
        </div>
      )}
      {successMsg && (
        <div className="alert alert-success" data-testid="handover-draft-saved-msg">
          <CheckCircle2 size={18} />
          <span>{successMsg}</span>
        </div>
      )}

      {/* STEP 5 REVIEW SCREEN BEFORE FINAL SUBMISSION */}
      {showReviewStep && (
        <div
          className="card"
          style={{
            marginBottom: "1.5rem",
            border: "2px solid var(--teal-600)",
            backgroundColor: "var(--teal-50)",
          }}
          data-testid="pre-submission-review-panel"
        >
          <div className="card-header">
            <h2 className="card-title" style={{ color: "var(--teal-700)" }}>
              Step 5: Pre-Submission Handover Verification
            </h2>
            <button
              type="button"
              className="btn btn-secondary btn-sm"
              onClick={() => setShowReviewStep(false)}
            >
              Return to Editing
            </button>
          </div>
          <p style={{ fontSize: "0.875rem", marginBottom: "1rem", color: "var(--navy-800)" }}>
            Please verify all recorded tasks, priorities, equipment statuses, and safety observations. Once submitted, this handover report will be locked and dispatched to the designated incoming worker for formal acknowledgment.
          </p>
          <div className="grid-3" style={{ marginBottom: "1rem", fontSize: "0.85rem" }}>
            <div>
              <strong>Selected Shift:</strong> {selectedShift?.name} ({selectedShift?.shift_date})
            </div>
            <div>
              <strong>Outgoing Worker:</strong> {user?.full_name}
            </div>
            <div>
              <strong>Designated Incoming Worker:</strong>{" "}
              {colleagues.find((c) => c.id === incomingWorkerId)?.full_name || "Selected"}
            </div>
          </div>
          <div style={{ marginBottom: "1rem", fontSize: "0.85rem" }}>
            <strong>Equipment Status:</strong> <EquipmentStatusBadge status={equipmentStatus} />{" "}
            {equipmentDetails && <span>— {equipmentDetails}</span>}
          </div>
          {safetyIssues && (
            <div className="alert alert-warning" style={{ marginBottom: "1rem" }}>
              <ShieldAlert size={16} />
              <span>
                <strong>Safety Issues / Near Misses:</strong> {safetyIssues}
              </span>
            </div>
          )}
          <div style={{ display: "flex", gap: "0.75rem", justifyContent: "flex-end" }}>
            <button
              type="button"
              className="btn btn-secondary"
              onClick={() => setShowReviewStep(false)}
            >
              Back to Draft
            </button>
            <button
              type="button"
              className="btn btn-primary"
              onClick={handleFormalSubmit}
              disabled={saving}
              data-testid="confirm-formal-submit-btn"
            >
              <Send size={16} />
              <span>{saving ? "Submitting..." : "Confirm & Formally Submit Handover"}</span>
            </button>
          </div>
        </div>
      )}

      {/* STEP 1: SELECT SHIFT & DESIGNATE INCOMING WORKER */}
      <div className="card" style={{ marginBottom: "1.25rem" }}>
        <h2 className="card-title" style={{ marginBottom: "0.85rem" }}>
          Step 1: Shift Context & Responsibility Transfer
        </h2>
        <div className="grid-3">
          <div className="form-group">
            <label htmlFor="select-shift" className="form-label">
              Active / Assigned Shift
            </label>
            <select
              id="select-shift"
              className="form-control"
              value={selectedShiftId}
              onChange={(e) => handleShiftChange(e.target.value)}
              data-testid="handover-shift-select"
            >
              <option value="">-- Select Shift --</option>
              {shifts.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.name} ({s.shift_date} {s.start_time.slice(0, 5)}-{s.end_time.slice(0, 5)})
                </option>
              ))}
            </select>
          </div>

          <div className="form-group">
            <label className="form-label">Submitting Outgoing Worker (Authenticated)</label>
            <input
              type="text"
              className="form-control"
              value={`${user?.full_name} (${user?.email})`}
              disabled
            />
          </div>

          <div className="form-group">
            <label htmlFor="select-incoming" className="form-label">
              Designated Incoming Worker
            </label>
            <select
              id="select-incoming"
              className="form-control"
              value={incomingWorkerId}
              onChange={(e) => setIncomingWorkerId(e.target.value)}
              data-testid="handover-incoming-select"
            >
              <option value="">-- Select Incoming Worker --</option>
              {colleagues
                .filter((c) => c.id !== user?.id)
                .map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.full_name} ({c.role_display} • {c.department})
                  </option>
                ))}
            </select>
          </div>
        </div>

        {selectedShift && (
          <div
            style={{
              padding: "0.65rem 0.9rem",
              borderRadius: "7px",
              backgroundColor: "var(--slate-50)",
              border: "1px solid var(--slate-200)",
              fontSize: "0.82rem",
              display: "flex",
              gap: "1.5rem",
              flexWrap: "wrap",
            }}
          >
            <span>
              <strong>Shift Date:</strong> {selectedShift.shift_date}
            </span>
            <span>
              <strong>Window:</strong> {selectedShift.start_time.slice(0, 5)} –{" "}
              {selectedShift.end_time.slice(0, 5)}
            </span>
            <span>
              <strong>Department:</strong> {selectedShift.department}
            </span>
            <span>
              <strong>Scheduled Outgoing:</strong> {selectedShift.outgoing_worker_name}
            </span>
            <span>
              <strong>Scheduled Incoming:</strong> {selectedShift.incoming_worker_name}
            </span>
          </div>
        )}
      </div>

      {/* STEP 2 & 3: RECORD SHIFT TASKS WITH NLP CATEGORISATION & PRIORITY DETECTION */}
      <div className="card" style={{ marginBottom: "1.25rem" }}>
        <div className="card-header">
          <h2 className="card-title" style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
            <BrainCircuit size={19} color="var(--teal-600)" />
            <span>Step 2 & 3: Record Shift Task & Run NLP Classification</span>
          </h2>
          <span className="badge badge-teal">
            Hugging Face Transformer + Manual Override
          </span>
        </div>

        <div className="form-group">
          <label htmlFor="task-desc-input" className="form-label">
            Task Description (Natural Language)
          </label>
          <div style={{ display: "flex", gap: "0.6rem" }}>
            <textarea
              id="task-desc-input"
              className="form-control"
              rows={2}
              placeholder="e.g., Major safety alert: jet fuel seepage detected at engine pylon fuel disconnect coupling; aircraft grounded pending seal swap."
              value={taskDesc}
              onChange={(e) => setTaskDesc(e.target.value)}
              data-testid="task-description-input"
            />
            <button
              type="button"
              className="btn btn-navy"
              style={{ flexShrink: 0 }}
              onClick={handleRunNLP}
              disabled={nlpRunning}
              data-testid="run-nlp-button"
            >
              <Sparkles size={15} />
              <span>{nlpRunning ? "Classifying..." : "Suggest Category & Priority (NLP)"}</span>
            </button>
          </div>
        </div>

        {suggestedCat && (
          <div
            style={{
              padding: "0.75rem 1rem",
              borderRadius: "8px",
              backgroundColor: isLowConf ? "var(--amber-50)" : "var(--teal-50)",
              border: `1px solid ${isLowConf ? "#fde68a" : "#99f6e4"}`,
              marginBottom: "1rem",
              fontSize: "0.84rem",
            }}
            data-testid="nlp-suggestion-banner"
          >
            <div style={{ display: "flex", justifyContent: "space-between", flexWrap: "wrap", gap: "0.5rem" }}>
              <div>
                <strong>NLP Model Suggestion:</strong> Category ={" "}
                <span className="badge badge-teal">{suggestedCat}</span> ({catConf}%) • Priority ={" "}
                <PriorityBadge priority={suggestedPrio} /> ({prioConf}%)
              </div>
              <span className="mono" style={{ fontSize: "0.75rem", color: "var(--slate-600)" }}>
                Provider: {nlpProvider} | Combined Confidence: {confScore}%
              </span>
            </div>
            {nlpWarning && (
              <div style={{ marginTop: "0.35rem", color: "var(--amber-700)", fontWeight: 600 }}>
                ⚠️ {nlpWarning}
              </div>
            )}
          </div>
        )}

        {!suggestedCat && nlpWarning && (
          <div className="alert alert-warning" data-testid="nlp-warning-alert">
            <AlertTriangle size={16} />
            <span>{nlpWarning}</span>
          </div>
        )}

        <div className="grid-3">
          <div className="form-group">
            <label htmlFor="task-cat-select" className="form-label">
              Confirmed Task Category (Accept or Override)
            </label>
            <select
              id="task-cat-select"
              className="form-control"
              value={taskCategory}
              onChange={(e) => setTaskCategory(e.target.value)}
              data-testid="task-category-select"
            >
              {categories.map((cat) => (
                <option key={cat} value={cat}>
                  {cat}
                </option>
              ))}
            </select>
          </div>

          <div className="form-group">
            <label htmlFor="task-prio-select" className="form-label">
              Confirmed Task Priority (Accept or Override)
            </label>
            <select
              id="task-prio-select"
              className="form-control"
              value={taskPriority}
              onChange={(e) => setTaskPriority(e.target.value)}
              data-testid="task-priority-select"
            >
              {priorities.map((pr) => (
                <option key={pr} value={pr}>
                  {pr}
                </option>
              ))}
            </select>
          </div>

          <div className="form-group">
            <label htmlFor="task-status-select" className="form-label">
              Task Status
            </label>
            <select
              id="task-status-select"
              className="form-control"
              value={taskStatus}
              onChange={(e) => setTaskStatus(e.target.value)}
              data-testid="task-status-select"
            >
              <option value="Pending">Pending</option>
              <option value="In Progress">In Progress</option>
              <option value="Completed">Completed</option>
            </select>
          </div>
        </div>

        <div className="grid-2">
          <div className="form-group">
            <label htmlFor="task-notes-input" className="form-label">
              Optional Contextual Notes / Handover Instructions
            </label>
            <input
              id="task-notes-input"
              type="text"
              className="form-control"
              placeholder="Part numbers, tooling location, or follow-up steps..."
              value={taskNotes}
              onChange={(e) => setTaskNotes(e.target.value)}
              data-testid="task-notes-input"
            />
          </div>

          <div className="form-group">
            <label htmlFor="task-due-input" className="form-label">
              Optional Target Due Date / Time
            </label>
            <input
              id="task-due-input"
              type="datetime-local"
              className="form-control"
              value={taskDueDate}
              onChange={(e) => setTaskDueDate(e.target.value)}
            />
          </div>
        </div>

        <button
          type="button"
          className="btn btn-primary"
          onClick={handleAddTaskToReport}
          data-testid="add-task-to-handover-btn"
        >
          <Plus size={16} />
          <span>Add Task to Handover Report</span>
        </button>

        {/* Recorded Tasks Table */}
        <div style={{ marginTop: "1.5rem" }}>
          <h3 style={{ fontSize: "0.95rem", fontWeight: 700, marginBottom: "0.65rem" }}>
            Recorded Shift Tasks in This Handover ({tasks.length})
          </h3>
          {tasks.length === 0 ? (
            <p style={{ fontSize: "0.85rem", color: "var(--slate-500)" }}>
              No tasks added yet. Enter a task description above and click "Add Task to Handover Report".
            </p>
          ) : (
            <div className="table-wrap">
              <table className="data-table" data-testid="handover-tasks-table">
                <thead>
                  <tr>
                    <th>Description & Notes</th>
                    <th>NLP Suggestion</th>
                    <th>Confirmed Category</th>
                    <th>Confirmed Priority</th>
                    <th>Status</th>
                    <th>Remove</th>
                  </tr>
                </thead>
                <tbody>
                  {tasks.map((tk, idx) => (
                    <tr key={tk.id || idx}>
                      <td>
                        <div style={{ fontWeight: 600 }}>{tk.description}</div>
                        {tk.contextual_notes && (
                          <div style={{ fontSize: "0.78rem", color: "var(--slate-500)" }}>
                            Note: {tk.contextual_notes}
                          </div>
                        )}
                      </td>
                      <td style={{ fontSize: "0.78rem" }}>
                        {tk.model_suggested_category ? (
                          <div>
                            <div>
                              Suggested: <strong>{tk.model_suggested_category}</strong> /{" "}
                              <strong>{tk.model_suggested_priority}</strong>
                            </div>
                            {tk.confidence_score != null && (
                              <div style={{ color: "var(--slate-500)" }}>
                                Confidence: {tk.confidence_score}%
                              </div>
                            )}
                          </div>
                        ) : (
                          <span style={{ color: "var(--slate-400)" }}>Manual Entry</span>
                        )}
                      </td>
                      <td>
                        <select
                          className="form-control"
                          style={{ padding: "0.25rem 0.5rem", fontSize: "0.8rem" }}
                          value={tk.confirmed_category}
                          onChange={(e) =>
                            handleUpdateQueuedTask(idx, "confirmed_category", e.target.value)
                          }
                        >
                          {categories.map((c) => (
                            <option key={c} value={c}>
                              {c}
                            </option>
                          ))}
                        </select>
                      </td>
                      <td>
                        <select
                          className="form-control"
                          style={{ padding: "0.25rem 0.5rem", fontSize: "0.8rem" }}
                          value={tk.confirmed_priority}
                          onChange={(e) =>
                            handleUpdateQueuedTask(idx, "confirmed_priority", e.target.value)
                          }
                        >
                          {priorities.map((p) => (
                            <option key={p} value={p}>
                              {p}
                            </option>
                          ))}
                        </select>
                      </td>
                      <td>
                        <select
                          className="form-control"
                          style={{ padding: "0.25rem 0.5rem", fontSize: "0.8rem" }}
                          value={tk.status}
                          onChange={(e) =>
                            handleUpdateQueuedTask(idx, "status", e.target.value)
                          }
                        >
                          <option value="Pending">Pending</option>
                          <option value="In Progress">In Progress</option>
                          <option value="Completed">Completed</option>
                        </select>
                      </td>
                      <td>
                        <button
                          type="button"
                          className="btn btn-danger btn-sm"
                          onClick={() => handleRemoveTask(idx)}
                          aria-label="Remove Task"
                        >
                          <Trash2 size={14} />
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>

      {/* EQUIPMENT STATUS, SAFETY ISSUES & CONTEXTUAL NOTES */}
      <div className="card">
        <h2 className="card-title" style={{ marginBottom: "0.85rem" }}>
          Equipment Status, Safety Issues & Contextual Handover Notes
        </h2>
        <div className="grid-2">
          <div className="form-group">
            <label htmlFor="equip-status" className="form-label">
              Overall Equipment & Tooling Status
            </label>
            <select
              id="equip-status"
              className="form-control"
              value={equipmentStatus}
              onChange={(e) => setEquipmentStatus(e.target.value)}
            >
              <option value="OPERATIONAL">All Systems Operational</option>
              <option value="MINOR_ISSUE">Minor Issue / Degraded Performance</option>
              <option value="MAINTENANCE_REQUIRED">Maintenance Required</option>
              <option value="CRITICAL_FAULT">Critical Fault / Equipment Grounded</option>
            </select>
          </div>

          <div className="form-group">
            <label htmlFor="equip-details" className="form-label">
              Equipment Status Details
            </label>
            <input
              id="equip-details"
              type="text"
              className="form-control"
              placeholder="Specify tagged equipment, test rigs, or calibration statuses..."
              value={equipmentDetails}
              onChange={(e) => setEquipmentDetails(e.target.value)}
            />
          </div>
        </div>

        <div className="form-group">
          <label htmlFor="safety-issues" className="form-label">
            Safety Issues, Hazards & Near Misses
          </label>
          <textarea
            id="safety-issues"
            className="form-control"
            rows={2}
            placeholder="Document any safety hazards, spills, lock-out/tag-out states, or near misses..."
            value={safetyIssues}
            onChange={(e) => setSafetyIssues(e.target.value)}
            data-testid="safety-issues-input"
          />
        </div>

        <div className="form-group">
          <label htmlFor="additional-notes" className="form-label">
            General Shift Handover Notes
          </label>
          <textarea
            id="additional-notes"
            className="form-control"
            rows={2}
            placeholder="General context for the incoming worker..."
            value={additionalNotes}
            onChange={(e) => setAdditionalNotes(e.target.value)}
          />
        </div>
      </div>
    </div>
  );
};

/* ============================================================================
   PAGE 11: LOG SHIFT ACTIVITY (/activity/log)
   ============================================================================ */
export const LogShiftActivityPage: React.FC = () => {
  const [narrative, setNarrative] = useState("");
  const [extractedTasks, setExtractedTasks] = useState<any[]>([]);
  const [shifts, setShifts] = useState<any[]>([]);
  const [selectedShift, setSelectedShift] = useState("");
  const [loading, setLoading] = useState(false);
  const [savedMsg, setSavedMsg] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    apiClient.get("/shifts/").then((res) => {
      const list = res.data.results || res.data || [];
      setShifts(list);
      if (list.length > 0) setSelectedShift(list[0].id);
    });
  }, []);

  const handleAnalyzeNarrative = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSavedMsg(null);
    if (!narrative.trim()) {
      setError("Please enter shift activity notes to analyze.");
      return;
    }
    setLoading(true);
    try {
      const res = await apiClient.post("/nlp/analyze-log/", {
        shift_notes: narrative,
      });
      setExtractedTasks(res.data.tasks || []);
    } catch (err: any) {
      setError(err.response?.data?.detail || "NLP log analysis failed.");
    } finally {
      setLoading(false);
    }
  };

  const handleSaveExtractedTasks = async () => {
    if (!selectedShift || extractedTasks.length === 0) return;
    setLoading(true);
    setError(null);
    try {
      for (const item of extractedTasks) {
        await apiClient.post("/tasks/", {
          shift: selectedShift,
          description: item.task,
          status: item.suggested_status || "Pending",
          category: item.category,
          priority: item.priority,
          confirmed_category: item.category,
          confirmed_priority: item.priority,
          model_suggested_category: item.category,
          model_suggested_priority: item.priority,
          category_confidence: item.category_confidence,
          priority_confidence: item.priority_confidence,
          confidence_score: item.confidence_score,
          nlp_provider_used: item.provider,
        });
      }
      setSavedMsg(
        `Successfully logged ${extractedTasks.length} NLP-classified task(s) to shift.`
      );
      setExtractedTasks([]);
      setNarrative("");
    } catch {
      setError("Failed to save one or more tasks to the shift.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <div style={{ marginBottom: "1.25rem" }}>
        <h1 style={{ fontSize: "1.4rem", fontWeight: 700 }}>
          Log Shift Activity (Multi-Task NLP Narrative Analyzer)
        </h1>
        <p style={{ fontSize: "0.85rem", color: "var(--slate-500)" }}>
          Enter free-text shift activity logs to automatically segment, classify, and record discrete operational tasks
        </p>
      </div>

      {savedMsg && (
        <div className="alert alert-success">
          <CheckCircle2 size={16} />
          <span>{savedMsg}</span>
        </div>
      )}
      {error && (
        <div className="alert alert-error">
          <AlertTriangle size={16} />
          <span>{error}</span>
        </div>
      )}

      <div className="card" style={{ marginBottom: "1.25rem" }}>
        <form onSubmit={handleAnalyzeNarrative}>
          <div className="form-group">
            <label className="form-label">Target Shift</label>
            <select
              className="form-control"
              value={selectedShift}
              onChange={(e) => setSelectedShift(e.target.value)}
            >
              {shifts.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.name} ({s.shift_date})
                </option>
              ))}
            </select>
          </div>
          <div className="form-group">
            <label className="form-label">Shift Activity Narrative</label>
            <textarea
              className="form-control"
              rows={4}
              placeholder="e.g., Checked Boeing 787 left engine oil pressure sensor readings, rectified TechLog snag #4412 on VHF Comm #1, and archived TechLog page #4412."
              value={narrative}
              onChange={(e) => setNarrative(e.target.value)}
            />
          </div>
          <button type="submit" className="btn btn-primary" disabled={loading}>
            <Sparkles size={16} />
            <span>{loading ? "Analyzing with NLP..." : "Segment & Classify Tasks"}</span>
          </button>
        </form>
      </div>

      {extractedTasks.length > 0 && (
        <div className="card">
          <div className="card-header">
            <h2 className="card-title">
              Detected Shift Tasks ({extractedTasks.length})
            </h2>
            <button
              type="button"
              className="btn btn-success btn-sm"
              onClick={handleSaveExtractedTasks}
              disabled={loading}
            >
              <Save size={15} />
              <span>Save All {extractedTasks.length} Tasks to Shift</span>
            </button>
          </div>
          <div className="table-wrap">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Segmented Task Description</th>
                  <th>Suggested Category</th>
                  <th>Suggested Priority</th>
                  <th>Confidence</th>
                  <th>Suggested Status</th>
                </tr>
              </thead>
              <tbody>
                {extractedTasks.map((tk, idx) => (
                  <tr key={idx}>
                    <td style={{ fontWeight: 600 }}>{tk.task}</td>
                    <td>{tk.category}</td>
                    <td>
                      <PriorityBadge priority={tk.priority} />
                    </td>
                    <td className="mono">{tk.confidence_score}%</td>
                    <td>
                      <TaskStatusBadge status={tk.suggested_status} />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};

/* ============================================================================
   PAGE 12: TASK TRACKING (/tasks)
   ============================================================================ */
export const TaskTrackingPage: React.FC = () => {
  const [tasks, setTasks] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [unresolvedOnly, setUnresolvedOnly] = useState(false);
  const [carriedForwardOnly, setCarriedForwardOnly] = useState(false);
  const [priorityFilter, setPriorityFilter] = useState("");
  const [selectedTaskHistory, setSelectedTaskHistory] = useState<any | null>(null);
  const [statusComment, setStatusComment] = useState("");

  const loadTasks = async () => {
    setLoading(true);
    try {
      const params: Record<string, string> = {};
      if (unresolvedOnly) params.unresolved_only = "true";
      if (carriedForwardOnly) params.carried_forward = "true";
      if (priorityFilter) params.priority = priorityFilter;
      const res = await apiClient.get("/tasks/", { params });
      setTasks(res.data.results || res.data || []);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadTasks();
  }, [unresolvedOnly, carriedForwardOnly, priorityFilter]);

  const handleStatusChange = async (taskId: string, newStatus: string) => {
    await apiClient.post(`/tasks/${taskId}/update-status/`, {
      status: newStatus,
      comment: statusComment || `Updated task status to ${newStatus}.`,
    });
    setStatusComment("");
    loadTasks();
  };

  return (
    <div>
      <div className="card-header" style={{ marginBottom: "1.25rem" }}>
        <div>
          <h1 style={{ fontSize: "1.4rem", fontWeight: 700 }}>
            Operational Task Tracking & Carry-Forward Queue
          </h1>
          <p style={{ fontSize: "0.85rem", color: "var(--slate-500)" }}>
            Monitor pending, in-progress, and carried-forward tasks across shifts with full audit history
          </p>
        </div>

        <div style={{ display: "flex", gap: "0.5rem", flexWrap: "wrap" }}>
          <button
            type="button"
            className={`btn btn-sm ${unresolvedOnly ? "btn-primary" : "btn-secondary"}`}
            onClick={() => setUnresolvedOnly(!unresolvedOnly)}
          >
            {unresolvedOnly ? "Unresolved Only" : "All Task Statuses"}
          </button>
          <button
            type="button"
            className={`btn btn-sm ${carriedForwardOnly ? "btn-primary" : "btn-secondary"}`}
            onClick={() => setCarriedForwardOnly(!carriedForwardOnly)}
          >
            {carriedForwardOnly ? "Carried-Forward Only" : "Include All Shifts"}
          </button>
          <select
            className="form-control"
            style={{ width: "auto", padding: "0.3rem 0.6rem", fontSize: "0.8rem" }}
            value={priorityFilter}
            onChange={(e) => setPriorityFilter(e.target.value)}
          >
            <option value="">All Priorities</option>
            <option value="Critical">Critical</option>
            <option value="High">High</option>
            <option value="Medium">Medium</option>
            <option value="Low">Low</option>
          </select>
        </div>
      </div>

      {selectedTaskHistory && (
        <div className="card" style={{ marginBottom: "1.25rem", borderLeft: "4px solid var(--teal-600)" }}>
          <div className="card-header">
            <h2 className="card-title">
              Task Audit History: {selectedTaskHistory.description}
            </h2>
            <button
              type="button"
              className="btn btn-secondary btn-sm"
              onClick={() => setSelectedTaskHistory(null)}
            >
              Close History
            </button>
          </div>
          <div style={{ fontSize: "0.84rem", marginBottom: "0.75rem" }}>
            <strong>NLP Suggested:</strong> {selectedTaskHistory.model_suggested_category || "—"}{" "}
            / {selectedTaskHistory.model_suggested_priority || "—"} •{" "}
            <strong>Worker Confirmed:</strong> {selectedTaskHistory.confirmed_category} /{" "}
            {selectedTaskHistory.confirmed_priority}{" "}
            {selectedTaskHistory.was_overridden && (
              <span className="badge badge-amber">Manual Override Applied</span>
            )}
          </div>
          <div style={{ display: "flex", flexDirection: "column", gap: "0.5rem" }}>
            {(selectedTaskHistory.history || []).map((h: any) => (
              <div
                key={h.id}
                style={{
                  padding: "0.55rem 0.75rem",
                  borderRadius: "6px",
                  backgroundColor: "var(--slate-50)",
                  fontSize: "0.82rem",
                }}
              >
                <strong>{new Date(h.created_at).toLocaleString()}</strong> —{" "}
                <strong>{h.changed_by_name}</strong> ({h.changed_by_role}):{" "}
                {h.previous_status ? `${h.previous_status} → ` : ""}
                <strong>{h.new_status}</strong> — {h.comment}
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="card">
        {loading ? (
          <p style={{ padding: "2rem", textAlign: "center" }}>Loading tasks...</p>
        ) : tasks.length === 0 ? (
          <p style={{ padding: "2rem", textAlign: "center", color: "var(--slate-500)" }}>
            No tasks match your current filters.
          </p>
        ) : (
          <div className="table-wrap">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Task Description</th>
                  <th>Shift & Handover</th>
                  <th>Category (NLP vs Final)</th>
                  <th>Priority</th>
                  <th>Status</th>
                  <th>Update Status</th>
                  <th>History</th>
                </tr>
              </thead>
              <tbody>
                {tasks.map((tk) => (
                  <tr key={tk.id}>
                    <td>
                      <div style={{ fontWeight: 600 }}>{tk.description}</div>
                      {tk.contextual_notes && (
                        <div style={{ fontSize: "0.76rem", color: "var(--slate-500)" }}>
                          {tk.contextual_notes}
                        </div>
                      )}
                      {tk.is_carried_forward && (
                        <span
                          className="badge badge-amber"
                          style={{ marginTop: "0.25rem", fontSize: "0.68rem" }}
                        >
                          Carried Forward Across Shifts
                        </span>
                      )}
                    </td>
                    <td style={{ fontSize: "0.8rem" }}>
                      <div>{tk.shift_name}</div>
                      {tk.handover_code && (
                        <Link
                          to={`/handovers/${tk.handover_report}`}
                          className="mono"
                          style={{ color: "var(--teal-700)", fontWeight: 600 }}
                        >
                          {tk.handover_code}
                        </Link>
                      )}
                    </td>
                    <td style={{ fontSize: "0.8rem" }}>
                      <div>
                        <strong>{tk.category}</strong>
                      </div>
                      {tk.was_overridden && (
                        <span className="badge badge-slate" style={{ fontSize: "0.68rem" }}>
                          NLP Overridden
                        </span>
                      )}
                    </td>
                    <td>
                      <PriorityBadge priority={tk.priority} />
                    </td>
                    <td>
                      <TaskStatusBadge status={tk.status} />
                    </td>
                    <td>
                      <select
                        className="form-control"
                        style={{ width: "auto", padding: "0.25rem 0.5rem", fontSize: "0.78rem" }}
                        value={tk.status}
                        onChange={(e) => handleStatusChange(tk.id, e.target.value)}
                        aria-label={`Change status for ${tk.description}`}
                      >
                        <option value="Pending">Pending</option>
                        <option value="In Progress">In Progress</option>
                        <option value="Completed">Completed</option>
                      </select>
                    </td>
                    <td>
                      <button
                        type="button"
                        className="btn btn-secondary btn-sm"
                        onClick={() => setSelectedTaskHistory(tk)}
                      >
                        <History size={14} />
                        <span>Audit ({tk.history?.length || 0})</span>
                      </button>
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
   PAGE 13 & 17: HANDOVER REPORT DETAILS (/handovers/:id, /supervisor/history/:id)
   ============================================================================ */
export const HandoverReportDetailsPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const { user } = useAuth();
  const [report, setReport] = useState<any | null>(null);
  const [loading, setLoading] = useState(true);
  const [amendReason, setAmendReason] = useState("");
  const [amendDetails, setAmendDetails] = useState("");
  const [amendError, setAmendError] = useState<string | null>(null);
  const [amendSuccess, setAmendSuccess] = useState<string | null>(null);

  const loadReport = async () => {
    setLoading(true);
    try {
      const res = await apiClient.get(`/handovers/${id}/`);
      setReport(res.data);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadReport();
  }, [id]);

  const handleAddAmendment = async (e: React.FormEvent) => {
    e.preventDefault();
    setAmendError(null);
    setAmendSuccess(null);
    try {
      const res = await apiClient.post(`/handovers/${id}/amend/`, {
        amendment_reason: amendReason,
        amendment_details: amendDetails,
      });
      setReport(res.data);
      setAmendReason("");
      setAmendDetails("");
      setAmendSuccess("Official auditable amendment recorded.");
    } catch (err: any) {
      setAmendError(
        err.response?.data?.detail || "Failed to record handover amendment."
      );
    }
  };

  if (loading || !report) {
    return (
      <div className="card" style={{ padding: "2.5rem", textAlign: "center" }}>
        Loading handover report details...
      </div>
    );
  }

  const canAcknowledge =
    report.status === "SUBMITTED" &&
    (report.designated_incoming_worker === user?.id || user?.role === "ADMIN");

  const canAmend =
    report.status !== "DRAFT" &&
    (report.submitting_worker === user?.id ||
      user?.role === "SUPERVISOR" ||
      user?.role === "ADMIN");

  return (
    <div>
      <div className="card-header" style={{ marginBottom: "1.25rem" }}>
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: "0.65rem" }}>
            <h1 className="mono" style={{ fontSize: "1.45rem", fontWeight: 700 }}>
              {report.report_code}
            </h1>
            <HandoverStatusBadge status={report.status} />
          </div>
          <p style={{ fontSize: "0.85rem", color: "var(--slate-500)" }}>
            Shift: <strong>{report.shift_details?.name}</strong> ({report.shift_details?.shift_date})
          </p>
        </div>

        <div style={{ display: "flex", gap: "0.6rem" }}>
          {report.status === "DRAFT" &&
            (report.submitting_worker === user?.id || user?.role === "ADMIN") && (
              <Link to={`/handovers/${report.id}/edit`} className="btn btn-primary">
                <FileEdit size={16} />
                <span>Edit Draft</span>
              </Link>
            )}
          {canAcknowledge && (
            <Link
              to={`/handovers/${report.id}/acknowledge`}
              className="btn btn-primary"
              data-testid="goto-acknowledge-page-btn"
            >
              <ClipboardCheck size={16} />
              <span>Proceed to Formal Acknowledgment</span>
            </Link>
          )}
          <Link to="/handovers/history" className="btn btn-secondary">
            Back to History
          </Link>
        </div>
      </div>

      <div className="grid-2" style={{ marginBottom: "1.25rem" }}>
        <div className="card">
          <h2 className="card-title" style={{ marginBottom: "0.75rem" }}>
            Handover Chain of Custody & Timestamps
          </h2>
          <div style={{ display: "grid", gap: "0.5rem", fontSize: "0.875rem" }}>
            <div>
              <strong>Outgoing Submitting Worker:</strong> {report.submitting_worker_name} ({report.submitting_worker_email})
            </div>
            <div>
              <strong>Designated Incoming Worker:</strong>{" "}
              {report.designated_incoming_worker_name} ({report.designated_incoming_worker_email})
            </div>
            <div>
              <strong>Created At:</strong> {new Date(report.created_at).toLocaleString()}
            </div>
            <div>
              <strong>Submitted At:</strong>{" "}
              <span data-testid="detail-submitted-at">
                {report.submitted_at
                  ? new Date(report.submitted_at).toLocaleString()
                  : "Not yet submitted (Draft)"}
              </span>
            </div>
            <div>
              <strong>Acknowledged At:</strong>{" "}
              <span data-testid="detail-acknowledged-at">
                {report.acknowledged_at
                  ? `${new Date(report.acknowledged_at).toLocaleString()} by ${report.acknowledged_by_name}`
                  : "Awaiting explicit incoming worker acknowledgment"}
              </span>
            </div>
            {report.acknowledgment_notes && (
              <div
                style={{
                  marginTop: "0.35rem",
                  padding: "0.6rem",
                  borderRadius: "6px",
                  backgroundColor: "var(--green-50)",
                  border: "1px solid #bbf7d0",
                }}
              >
                <strong>Incoming Acknowledgment Sign-Off Note:</strong>{" "}
                {report.acknowledgment_notes}
              </div>
            )}
          </div>
        </div>

        <div className="card">
          <h2 className="card-title" style={{ marginBottom: "0.75rem" }}>
            Equipment Status & Safety Observations
          </h2>
          <div style={{ marginBottom: "0.65rem" }}>
            <EquipmentStatusBadge status={report.equipment_status} />
            {report.equipment_details && (
              <p style={{ fontSize: "0.85rem", marginTop: "0.35rem" }}>
                {report.equipment_details}
              </p>
            )}
          </div>
          <div style={{ marginBottom: "0.65rem", fontSize: "0.875rem" }}>
            <strong>Safety Issues / Near Misses:</strong>
            <p style={{ color: report.safety_issues ? "var(--red-700)" : "var(--slate-500)" }}>
              {report.safety_issues || "No safety incidents reported."}
            </p>
          </div>
          <div style={{ fontSize: "0.875rem" }}>
            <strong>Additional Handover Notes:</strong>
            <p style={{ color: "var(--slate-600)" }}>
              {report.additional_notes || "None."}
            </p>
          </div>
        </div>
      </div>

      {/* Tasks Table */}
      <div className="card" style={{ marginBottom: "1.25rem" }}>
        <h2 className="card-title" style={{ marginBottom: "0.85rem" }}>
          Recorded Shift Tasks ({report.tasks?.length || 0})
        </h2>
        <div className="table-wrap">
          <table className="data-table">
            <thead>
              <tr>
                <th>Task Description</th>
                <th>NLP Suggested</th>
                <th>Worker Confirmed Category</th>
                <th>Priority</th>
                <th>Task Status</th>
                <th>Notes</th>
              </tr>
            </thead>
            <tbody>
              {(report.tasks || []).map((tk: any) => (
                <tr key={tk.id}>
                  <td style={{ fontWeight: 600 }}>
                    {tk.description}
                    {tk.is_carried_forward && (
                      <div>
                        <span className="badge badge-amber" style={{ fontSize: "0.68rem", marginTop: "0.2rem" }}>
                          Carried Forward
                        </span>
                      </div>
                    )}
                  </td>
                  <td style={{ fontSize: "0.78rem", color: "var(--slate-600)" }}>
                    {tk.model_suggested_category ? (
                      <>
                        {tk.model_suggested_category} / {tk.model_suggested_priority}
                        {tk.confidence_score != null ? ` (${tk.confidence_score}%)` : ""}
                      </>
                    ) : (
                      "Manual"
                    )}
                  </td>
                  <td>
                    {tk.confirmed_category || tk.category}{" "}
                    {tk.was_overridden && (
                      <span className="badge badge-slate" style={{ fontSize: "0.65rem" }}>
                        Overridden
                      </span>
                    )}
                  </td>
                  <td>
                    <PriorityBadge priority={tk.confirmed_priority || tk.priority} />
                  </td>
                  <td>
                    <TaskStatusBadge status={tk.status} />
                  </td>
                  <td style={{ fontSize: "0.8rem" }}>{tk.contextual_notes || "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Amendments & Audit Trail */}
      {report.amendments?.length > 0 && (
        <div className="card" style={{ marginBottom: "1.25rem" }}>
          <h2 className="card-title" style={{ marginBottom: "0.75rem" }}>
            Official Post-Submission Amendments ({report.amendments.length})
          </h2>
          {report.amendments.map((am: any) => (
            <div
              key={am.id}
              style={{
                padding: "0.75rem",
                borderRadius: "6px",
                backgroundColor: "var(--amber-50)",
                border: "1px solid #fde68a",
                marginBottom: "0.5rem",
                fontSize: "0.85rem",
              }}
            >
              <strong>{new Date(am.created_at).toLocaleString()}</strong> —{" "}
              <strong>{am.author_name}</strong> ({am.author_role}):{" "}
              <strong>{am.amendment_reason}</strong> — {am.amendment_details}
            </div>
          ))}
        </div>
      )}

      {canAmend && (
        <div className="card">
          <h2 className="card-title" style={{ marginBottom: "0.5rem" }}>
            Record Auditable Post-Submission Amendment
          </h2>
          <p style={{ fontSize: "0.8rem", color: "var(--slate-500)", marginBottom: "0.85rem" }}>
            Submitted reports cannot be silently overwritten. Use this form to append a timestamped, auditable amendment.
          </p>
          {amendSuccess && <div className="alert alert-success">{amendSuccess}</div>}
          {amendError && <div className="alert alert-error">{amendError}</div>}
          <form onSubmit={handleAddAmendment}>
            <div className="grid-2">
              <div className="form-group">
                <label className="form-label">Amendment Reason</label>
                <input
                  type="text"
                  className="form-control"
                  placeholder="e.g., Updated Torque Verification Reading"
                  value={amendReason}
                  onChange={(e) => setAmendReason(e.target.value)}
                  required
                />
              </div>
              <div className="form-group">
                <label className="form-label">Amendment Details</label>
                <input
                  type="text"
                  className="form-control"
                  placeholder="Enter the supplemental operational note..."
                  value={amendDetails}
                  onChange={(e) => setAmendDetails(e.target.value)}
                  required
                />
              </div>
            </div>
            <button type="submit" className="btn btn-secondary btn-sm">
              Append Auditable Amendment
            </button>
          </form>
        </div>
      )}
    </div>
  );
};

/* ============================================================================
   PAGE 14: INCOMING HANDOVER REVIEW & EXPLICIT ACKNOWLEDGMENT
   (/handovers/incoming and /handovers/:id/acknowledge)
   ============================================================================ */
export const IncomingHandoverAcknowledgePage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const { user } = useAuth();
  const navigate = useNavigate();

  const [assignedHandovers, setAssignedHandovers] = useState<any[]>([]);
  const [selectedReport, setSelectedReport] = useState<any | null>(null);
  const [ackNotes, setAckNotes] = useState("");
  const [confirmedRead, setConfirmedRead] = useState(false);
  const [loading, setLoading] = useState(true);
  const [submittingAck, setSubmittingAck] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadData = async () => {
    setLoading(true);
    setError(null);
    try {
      if (id) {
        // Opening or viewing the handover report NEVER marks it acknowledged!
        const res = await apiClient.get(`/handovers/${id}/`);
        setSelectedReport(res.data);
      } else {
        const res = await apiClient.get("/handovers/", {
          params: { scope: "assigned_to_me" },
        });
        const list = res.data.results || res.data || [];
        setAssignedHandovers(list);
        const firstPending = list.find((h: any) => h.status === "SUBMITTED");
        if (firstPending) {
          setSelectedReport(firstPending);
        }
      }
    } catch (err: any) {
      setError(
        err.response?.data?.detail || "Unable to load handover report for review."
      );
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [id]);

  const handleExplicitAcknowledge = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedReport) return;
    if (!confirmedRead) {
      setError(
        "Please confirm that you have reviewed all tasks, equipment statuses, and safety notes before acknowledging."
      );
      return;
    }
    setSubmittingAck(true);
    setError(null);
    try {
      const res = await apiClient.post(
        `/handovers/${selectedReport.id}/acknowledge/`,
        { acknowledgment_notes: ackNotes }
      );
      setSelectedReport(res.data);
      navigate(`/handovers/${selectedReport.id}`);
    } catch (err: any) {
      setError(
        err.response?.data?.detail ||
          err.response?.data?.acknowledgment_notes?.[0] ||
          "Acknowledgment rejected by backend security policy."
      );
    } finally {
      setSubmittingAck(false);
    }
  };

  return (
    <div>
      <div className="card-header" style={{ marginBottom: "1.25rem" }}>
        <div>
          <h1 style={{ fontSize: "1.4rem", fontWeight: 700 }}>
            Incoming Handover Review & Explicit Acknowledgment
          </h1>
          <p style={{ fontSize: "0.85rem", color: "var(--slate-500)" }}>
            Review the outgoing worker's report, inspect unresolved and critical tasks, and formally sign off receipt
          </p>
        </div>
      </div>

      {error && (
        <div className="alert alert-error" role="alert" data-testid="ack-error-alert">
          <AlertTriangle size={18} />
          <span>{error}</span>
        </div>
      )}

      {!id && assignedHandovers.length > 0 && (
        <div className="card" style={{ marginBottom: "1.25rem" }}>
          <h2 className="card-title" style={{ marginBottom: "0.75rem" }}>
            Handovers Assigned to You ({assignedHandovers.length})
          </h2>
          <div className="table-wrap">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Report Code</th>
                  <th>Shift</th>
                  <th>Outgoing Worker</th>
                  <th>Unresolved / Critical</th>
                  <th>Status</th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody>
                {assignedHandovers.map((h) => (
                  <tr key={h.id}>
                    <td className="mono" style={{ fontWeight: 700 }}>
                      {h.report_code}
                    </td>
                    <td>
                      {h.shift_details?.name} ({h.shift_details?.shift_date})
                    </td>
                    <td>{h.submitting_worker_name}</td>
                    <td>
                      {h.unresolved_tasks} unresolved ({h.critical_tasks} critical)
                    </td>
                    <td>
                      <HandoverStatusBadge status={h.status} />
                    </td>
                    <td>
                      <button
                        type="button"
                        className="btn btn-primary btn-sm"
                        onClick={() => setSelectedReport(h)}
                      >
                        Select for Review
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {loading ? (
        <div className="card" style={{ padding: "2rem", textAlign: "center" }}>
          Loading handover report...
        </div>
      ) : !selectedReport ? (
        <div className="card" style={{ padding: "2.5rem", textAlign: "center", color: "var(--slate-500)" }}>
          No pending handovers currently assigned to you.
        </div>
      ) : (
        <div className="card" data-testid="incoming-review-card">
          <div className="card-header">
            <div>
              <h2 className="card-title">
                Reviewing Report:{" "}
                <span className="mono">{selectedReport.report_code}</span>
              </h2>
              <div style={{ fontSize: "0.82rem", color: "var(--slate-500)" }}>
                Submitted by <strong>{selectedReport.submitting_worker_name}</strong> at{" "}
                {selectedReport.submitted_at
                  ? new Date(selectedReport.submitted_at).toLocaleString()
                  : "Draft"}
              </div>
            </div>
            <HandoverStatusBadge status={selectedReport.status} />
          </div>

          {selectedReport.safety_issues && (
            <div className="alert alert-error">
              <ShieldAlert size={18} />
              <div>
                <strong>Reported Safety Issue / Hazard:</strong>{" "}
                {selectedReport.safety_issues}
              </div>
            </div>
          )}

          <div className="grid-2" style={{ marginBottom: "1rem", fontSize: "0.875rem" }}>
            <div>
              <strong>Equipment Status:</strong>{" "}
              <EquipmentStatusBadge status={selectedReport.equipment_status} />
              {selectedReport.equipment_details && (
                <div style={{ marginTop: "0.25rem", color: "var(--slate-600)" }}>
                  {selectedReport.equipment_details}
                </div>
              )}
            </div>
            <div>
              <strong>General Shift Notes:</strong>
              <div style={{ color: "var(--slate-600)" }}>
                {selectedReport.additional_notes || "None."}
              </div>
            </div>
          </div>

          <h3 style={{ fontSize: "0.95rem", fontWeight: 700, marginBottom: "0.6rem" }}>
            Tasks Transferred in This Handover ({selectedReport.tasks?.length || 0})
          </h3>
          <div className="table-wrap" style={{ marginBottom: "1.25rem" }}>
            <table className="data-table">
              <thead>
                <tr>
                  <th>Task Description</th>
                  <th>Category</th>
                  <th>Priority</th>
                  <th>Status</th>
                  <th>Contextual Notes</th>
                </tr>
              </thead>
              <tbody>
                {(selectedReport.tasks || []).map((tk: any) => (
                  <tr key={tk.id}>
                    <td style={{ fontWeight: 600 }}>{tk.description}</td>
                    <td>{tk.confirmed_category || tk.category}</td>
                    <td>
                      <PriorityBadge priority={tk.confirmed_priority || tk.priority} />
                    </td>
                    <td>
                      <TaskStatusBadge status={tk.status} />
                    </td>
                    <td style={{ fontSize: "0.8rem" }}>{tk.contextual_notes || "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {selectedReport.status === "SUBMITTED" ? (
            <form
              onSubmit={handleExplicitAcknowledge}
              style={{
                padding: "1.25rem",
                borderRadius: "8px",
                backgroundColor: "var(--teal-50)",
                border: "1px solid #5eead4",
              }}
              data-testid="explicit-acknowledge-form"
            >
              <h3 style={{ fontSize: "1rem", fontWeight: 700, marginBottom: "0.5rem" }}>
                Formal Transfer of Responsibility Sign-Off
              </h3>
              <p style={{ fontSize: "0.84rem", color: "var(--slate-600)", marginBottom: "0.85rem" }}>
                Acknowledging this handover records your identity ({user?.full_name}) and UTC timestamp in the immutable audit log. Unfinished tasks (Pending / In Progress) will be carried forward into your shift without being marked completed.
              </p>

              <div className="form-group">
                <label htmlFor="ack-notes-input" className="form-label">
                  Incoming Worker Acknowledgment Notes
                </label>
                <textarea
                  id="ack-notes-input"
                  className="form-control"
                  rows={2}
                  placeholder="Confirm receipt of unresolved tasks, tooling, and safety instructions..."
                  value={ackNotes}
                  onChange={(e) => setAckNotes(e.target.value)}
                  data-testid="ack-notes-input"
                />
              </div>

              <div className="form-group" style={{ display: "flex", alignItems: "center", gap: "0.55rem" }}>
                <input
                  id="confirm-review-checkbox"
                  type="checkbox"
                  checked={confirmedRead}
                  onChange={(e) => setConfirmedRead(e.target.checked)}
                  data-testid="confirm-review-checkbox"
                />
                <label htmlFor="confirm-review-checkbox" style={{ fontSize: "0.85rem", fontWeight: 600 }}>
                  I have inspected all recorded tasks, critical priorities, equipment statuses, and safety issues.
                </label>
              </div>

              <button
                type="submit"
                className="btn btn-primary"
                disabled={submittingAck}
                data-testid="submit-explicit-ack-btn"
              >
                <FileCheck2 size={17} />
                <span>
                  {submittingAck
                    ? "Recording Formal Acknowledgment..."
                    : "Formally Acknowledge Handover Receipt"}
                </span>
              </button>
            </form>
          ) : (
            <div className="alert alert-success">
              <CheckCircle2 size={18} />
              <span>
                This handover report has already been formally acknowledged by{" "}
                <strong>{selectedReport.acknowledged_by_name}</strong> at{" "}
                {selectedReport.acknowledged_at
                  ? new Date(selectedReport.acknowledged_at).toLocaleString()
                  : ""}
                .
              </span>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
