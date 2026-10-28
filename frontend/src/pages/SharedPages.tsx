import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  AlertTriangle,
  ArrowRight,
  Bell,
  Calendar,
  CheckCheck,
  CheckCircle2,
  ClipboardCheck,
  Clock,
  FilePlus2,
  Filter,
  Plane,
  RefreshCw,
  Search,
  ShieldAlert,
  UserCheck,
} from "lucide-react";
import { apiClient } from "../api/client";
import { useAuth } from "../context/AuthContext";
import {
  EquipmentStatusBadge,
  HandoverStatusBadge,
  PriorityBadge,
  TaskStatusBadge,
} from "../components/Badges";

export const DashboardOverviewPage: React.FC<{
  forcedScope?: "personal" | "organisation";
  titleOverride?: string;
}> = ({ forcedScope, titleOverride }) => {
  const { user } = useAuth();
  const [data, setData] = useState<any | null>(null);
  const [dutyStatus, setDutyStatus] = useState<any | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [dateFrom, setDateFrom] = useState<string>("");
  const [dateTo, setDateTo] = useState<string>("");

  const fetchDutyStatus = async () => {
    try {
      const res = await apiClient.get("/shifts/my-duty/");
      setDutyStatus(res.data);
    } catch {
      // Duty status is non-blocking
    }
  };

  const fetchDashboard = async () => {
    setLoading(true);
    setError(null);
    try {
      const params: Record<string, string> = {};
      if (dateFrom) params.date_from = dateFrom;
      if (dateTo) params.date_to = dateTo;
      if (forcedScope) params.scope = forcedScope;
      const [resDash] = await Promise.all([
        apiClient.get("/analytics/dashboard/", { params }),
        fetchDutyStatus(),
      ]);
      setData(resDash.data);
    } catch (err: any) {
      setError(
        err.response?.data?.detail ||
          "Failed to load live dashboard metrics from backend."
      );
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboard();
  }, [dateFrom, dateTo, forcedScope]);

  const m = data?.metrics || {};

  return (
    <div>
      <div className="card-header" style={{ marginBottom: "1.25rem" }}>
        <div>
          <h1 style={{ fontSize: "1.45rem", fontWeight: 700 }}>
            {titleOverride ||
              (user?.role === "SUPERVISOR" || user?.role === "ADMIN"
                ? "Operational Command Dashboard"
                : "Shift Operations Dashboard")}
          </h1>
          <p style={{ fontSize: "0.85rem", color: "var(--slate-500)" }}>
            Live metrics calculated from PostgreSQL shift records ({data?.scope === "organisation" ? "Organisation-Wide Scope" : "Assigned Worker Scope"})
          </p>
        </div>

        <div style={{ display: "flex", alignItems: "center", gap: "0.6rem", flexWrap: "wrap" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "0.35rem" }}>
            <Calendar size={15} color="var(--slate-500)" />
            <input
              type="date"
              className="form-control"
              style={{ width: "auto", padding: "0.35rem 0.55rem", fontSize: "0.8rem" }}
              value={dateFrom}
              onChange={(e) => setDateFrom(e.target.value)}
              aria-label="Filter From Date"
            />
            <span style={{ color: "var(--slate-400)" }}>to</span>
            <input
              type="date"
              className="form-control"
              style={{ width: "auto", padding: "0.35rem 0.55rem", fontSize: "0.8rem" }}
              value={dateTo}
              onChange={(e) => setDateTo(e.target.value)}
              aria-label="Filter To Date"
            />
          </div>
          {(dateFrom || dateTo) && (
            <button
              type="button"
              className="btn btn-secondary btn-sm"
              onClick={() => {
                setDateFrom("");
                setDateTo("");
              }}
            >
              Clear Dates
            </button>
          )}
          <button
            type="button"
            className="btn btn-secondary btn-sm"
            onClick={fetchDashboard}
          >
            <RefreshCw size={14} />
            <span>Refresh</span>
          </button>
          {(user?.role === "OUTGOING_WORKER" || user?.role === "INCOMING_WORKER" || user?.role === "ADMIN") && (
            <>
              <Link to="/handovers/create" className="btn btn-primary btn-sm" data-testid="dashboard-create-handover-btn">
                <FilePlus2 size={15} />
                <span>New Handover Report</span>
              </Link>
              <Link to="/handovers/incoming" className="btn btn-navy btn-sm" data-testid="dashboard-incoming-queue-btn">
                <ClipboardCheck size={15} />
                <span>Review Incoming Handovers</span>
              </Link>
            </>
          )}
        </div>
      </div>

      {error && (
        <div className="alert alert-error" role="alert">
          <AlertTriangle size={18} />
          <span>{error}</span>
        </div>
      )}

      {/* Dynamic Operational Duty Status Banner */}
      {dutyStatus && dutyStatus.has_assignment && (
        <div
          className="duty-status-card"
          data-testid="shift-duty-banner"
          style={{
            marginBottom: "1.5rem",
            background: dutyStatus.is_outgoing
              ? "linear-gradient(135deg, rgba(200, 16, 46, 0.05) 0%, rgba(229, 168, 35, 0.06) 100%)"
              : "linear-gradient(135deg, rgba(10, 25, 47, 0.04) 0%, rgba(0, 122, 61, 0.06) 100%)",
            border: dutyStatus.is_outgoing
              ? "1px solid rgba(200, 16, 46, 0.3)"
              : "1px solid rgba(10, 25, 47, 0.25)",
            borderLeft: dutyStatus.is_outgoing
              ? "6px solid var(--kq-red-600)"
              : "6px solid var(--navy-900)",
            borderRadius: "10px",
            padding: "1.25rem 1.5rem",
            boxShadow: "0 2px 8px rgba(0, 0, 0, 0.04)",
          }}
        >
          <div
            style={{
              display: "flex",
              alignItems: "flex-start",
              justifyContent: "space-between",
              gap: "1.25rem",
              flexWrap: "wrap",
            }}
          >
            <div style={{ flex: "1 1 320px" }}>
              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: "0.55rem",
                  marginBottom: "0.45rem",
                  flexWrap: "wrap",
                }}
              >
                <span
                  style={{
                    backgroundColor: dutyStatus.is_outgoing
                      ? "var(--kq-red-600)"
                      : "var(--navy-900)",
                    color: "#fff",
                    fontWeight: 800,
                    fontSize: "0.76rem",
                    padding: "0.25rem 0.65rem",
                    borderRadius: "4px",
                    letterSpacing: "0.04em",
                    textTransform: "uppercase",
                    display: "inline-flex",
                    alignItems: "center",
                    gap: "0.35rem",
                  }}
                  data-testid="duty-role-badge"
                >
                  <UserCheck size={14} />
                  <span>
                    YOU ARE: {dutyStatus.is_outgoing ? "OUTGOING WORKER" : "INCOMING WORKER"}
                  </span>
                </span>
                {dutyStatus.is_active_now ? (
                  <span
                    style={{
                      background: "rgba(0, 122, 61, 0.12)",
                      color: "var(--green-700)",
                      fontWeight: 700,
                      fontSize: "0.72rem",
                      padding: "0.22rem 0.5rem",
                      borderRadius: "4px",
                      display: "inline-flex",
                      alignItems: "center",
                      gap: "0.25rem",
                    }}
                  >
                    <span
                      style={{
                        width: 6,
                        height: 6,
                        borderRadius: "50%",
                        backgroundColor: "var(--green-600)",
                        display: "inline-block",
                      }}
                    />
                    LIVE SHIFT ACTIVE NOW
                  </span>
                ) : (
                  <span
                    style={{
                      background: "rgba(229, 168, 35, 0.15)",
                      color: "var(--kq-gold-800)",
                      fontWeight: 700,
                      fontSize: "0.72rem",
                      padding: "0.22rem 0.5rem",
                      borderRadius: "4px",
                    }}
                  >
                    SCHEDULED SHIFT
                  </span>
                )}
              </div>

              <h2
                style={{
                  fontSize: "1.15rem",
                  fontWeight: 700,
                  color: "var(--navy-900)",
                  margin: "0 0 0.35rem 0",
                  display: "flex",
                  alignItems: "center",
                  gap: "0.45rem",
                }}
                data-testid="duty-shift-name"
              >
                <Plane size={18} color="var(--kq-red-600)" />
                <span>{dutyStatus.shift?.shift_name || "Assigned Shift Window"}</span>
              </h2>

              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: "1.2rem",
                  fontSize: "0.82rem",
                  color: "var(--slate-600)",
                  flexWrap: "wrap",
                }}
              >
                <span style={{ display: "inline-flex", alignItems: "center", gap: "0.3rem" }}>
                  <Clock size={14} color="var(--slate-500)" />
                  <strong>Shift Time:</strong> {dutyStatus.shift?.shift_date} (
                  {dutyStatus.shift?.start_time?.slice(0, 5)} – {dutyStatus.shift?.end_time?.slice(0, 5)})
                </span>
                {dutyStatus.shift?.department_display && (
                  <span>
                    <strong>Department:</strong> {dutyStatus.shift.department_display}
                  </span>
                )}
              </div>

              {/* Handover Partner Info */}
              {dutyStatus.partner_worker && (
                <div
                  style={{
                    marginTop: "0.75rem",
                    padding: "0.6rem 0.85rem",
                    background: "rgba(255, 255, 255, 0.85)",
                    border: "1px solid var(--slate-200)",
                    borderRadius: "6px",
                    display: "inline-flex",
                    alignItems: "center",
                    gap: "0.6rem",
                    fontSize: "0.83rem",
                    flexWrap: "wrap",
                  }}
                  data-testid="duty-partner-info"
                >
                  <span style={{ color: "var(--slate-500)", fontWeight: 600 }}>
                    {dutyStatus.is_outgoing ? "Handing Over To (Incoming Crew):" : "Taking Over From (Outgoing Crew):"}
                  </span>
                  <strong style={{ color: "var(--navy-900)" }}>
                    {dutyStatus.partner_worker.full_name}
                  </strong>
                  <span style={{ color: "var(--slate-500)", fontSize: "0.78rem" }}>
                    ({dutyStatus.partner_worker.email} • {dutyStatus.partner_worker.employee_id})
                  </span>
                </div>
              )}
            </div>

            {/* Quick Action Button */}
            <div
              style={{
                display: "flex",
                flexDirection: "column",
                alignItems: "flex-end",
                justifyContent: "center",
                gap: "0.5rem",
                alignSelf: "center",
              }}
            >
              {dutyStatus.suggested_url && (
                <Link
                  to={dutyStatus.suggested_url}
                  className={dutyStatus.is_outgoing ? "btn btn-primary" : "btn btn-navy"}
                  style={{
                    padding: "0.7rem 1.15rem",
                    fontSize: "0.88rem",
                    fontWeight: 700,
                    display: "inline-flex",
                    alignItems: "center",
                    gap: "0.45rem",
                    boxShadow: "0 2px 4px rgba(0,0,0,0.1)",
                  }}
                  data-testid="duty-action-button"
                >
                  <span>{dutyStatus.suggested_action_label || (dutyStatus.is_outgoing ? "Record Tasks & Create Handover" : "Review Incoming Handovers")}</span>
                  <ArrowRight size={16} />
                </Link>
              )}
              {dutyStatus.handover && (
                <span style={{ fontSize: "0.75rem", color: "var(--slate-500)" }}>
                  Current Report: <strong>{dutyStatus.handover.report_code}</strong> ({dutyStatus.handover.status_display})
                </span>
              )}
            </div>
          </div>
        </div>
      )}

      {loading && !data ? (
        <div className="card" style={{ textAlign: "center", padding: "3rem" }}>
          Calculating real-time shift metrics from PostgreSQL...
        </div>
      ) : (
        <>
          {/* 6 Required Metric Cards */}
          <div className="metrics-grid" data-testid="dashboard-metrics-grid">
            <div className="metric-card">
              <span className="metric-label">Active Shifts</span>
              <span className="metric-value" data-testid="metric-active-shifts">
                {m.active_shifts ?? 0}
              </span>
              <span className="metric-sub">
                {m.scheduled_shifts ?? 0} scheduled upcoming
              </span>
            </div>

            <div className="metric-card amber">
              <span className="metric-label">Awaiting Acknowledgment</span>
              <span className="metric-value" data-testid="metric-awaiting-ack">
                {m.handovers_awaiting_acknowledgment ?? 0}
              </span>
              <span className="metric-sub">
                Requires explicit incoming sign-off
              </span>
            </div>

            <div className="metric-card navy">
              <span className="metric-label">Submitted Handovers</span>
              <span className="metric-value" data-testid="metric-submitted-handovers">
                {m.submitted_handovers ?? 0}
              </span>
              <span className="metric-sub">
                {m.acknowledged_handovers ?? 0} acknowledged • {m.draft_handovers ?? 0} drafts
              </span>
            </div>

            <div className="metric-card amber">
              <span className="metric-label">Unresolved Tasks</span>
              <span className="metric-value" data-testid="metric-unresolved-tasks">
                {m.unresolved_tasks ?? 0}
              </span>
              <span className="metric-sub">
                {m.carried_forward_tasks ?? 0} carried forward across shifts
              </span>
            </div>

            <div className="metric-card red">
              <span className="metric-label">Critical-Priority Tasks</span>
              <span className="metric-value" data-testid="metric-critical-tasks">
                {m.critical_priority_tasks ?? 0}
              </span>
              <span className="metric-sub">
                Unresolved high-risk items
              </span>
            </div>

            <div className="metric-card green">
              <span className="metric-label">Handover Completion Rate</span>
              <span className="metric-value" data-testid="metric-completion-rate">
                {m.handover_completion_rate ?? 0}%
              </span>
              <span className="metric-sub">
                {m.completion_rate_numerator ?? 0} of {m.completion_rate_denominator ?? 0} submitted acknowledged
              </span>
            </div>
          </div>

          {/* Critical Issues & Completion Trend Chart */}
          <div className="grid-2" style={{ marginBottom: "1.5rem" }}>
            <div className="card">
              <div className="card-header">
                <h2 className="card-title" style={{ display: "flex", alignItems: "center", gap: "0.45rem" }}>
                  <ShieldAlert size={18} color="var(--red-600)" />
                  <span>Critical Issues & Safety Alerts Requiring Attention</span>
                </h2>
              </div>
              {data?.critical_tasks?.length === 0 &&
              data?.safety_and_equipment_alerts?.length === 0 ? (
                <p style={{ fontSize: "0.875rem", color: "var(--slate-500)" }}>
                  No unresolved critical tasks or safety incidents in the selected range.
                </p>
              ) : (
                <div style={{ display: "flex", flexDirection: "column", gap: "0.65rem" }}>
                  {data?.critical_tasks?.map((ct: any) => (
                    <div
                      key={ct.id}
                      style={{
                        padding: "0.75rem",
                        borderRadius: "8px",
                        backgroundColor: "var(--red-50)",
                        border: "1px solid #fecaca",
                      }}
                    >
                      <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "0.3rem" }}>
                        <PriorityBadge priority={ct.priority} />
                        <TaskStatusBadge status={ct.status} />
                      </div>
                      <div style={{ fontWeight: 600, fontSize: "0.875rem", color: "var(--navy-900)" }}>
                        {ct.description}
                      </div>
                      <div style={{ fontSize: "0.75rem", color: "var(--slate-600)", marginTop: "0.25rem" }}>
                        Category: <strong>{ct.category}</strong> • Shift: {ct.shift_name}
                      </div>
                    </div>
                  ))}
                  {data?.safety_and_equipment_alerts?.map((al: any) => (
                    <div
                      key={al.handover_id}
                      style={{
                        padding: "0.75rem",
                        borderRadius: "8px",
                        backgroundColor: "var(--amber-50)",
                        border: "1px solid #fde68a",
                      }}
                    >
                      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                        <Link
                          to={`/handovers/${al.handover_id}`}
                          style={{ fontWeight: 700, color: "var(--navy-900)" }}
                        >
                          {al.report_code} — {al.shift_name}
                        </Link>
                        <EquipmentStatusBadge status={al.equipment_status} />
                      </div>
                      {al.safety_issues && (
                        <p style={{ fontSize: "0.8rem", color: "var(--amber-700)", marginTop: "0.3rem" }}>
                          Safety Note: {al.safety_issues}
                        </p>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>

            <div className="card">
              <div className="card-header">
                <h2 className="card-title">Handover Completion Rate Over Time</h2>
                <span style={{ fontSize: "0.75rem", color: "var(--slate-500)" }}>
                  Acknowledged vs Submitted by Shift Date
                </span>
              </div>
              {!data?.completion_trend?.length ? (
                <p style={{ fontSize: "0.875rem", color: "var(--slate-500)" }}>
                  No handover trend data available for the selected date range.
                </p>
              ) : (
                <div style={{ display: "flex", flexDirection: "column", gap: "0.75rem" }}>
                  {data.completion_trend.map((pt: any) => (
                    <div key={pt.date}>
                      <div
                        style={{
                          display: "flex",
                          justifyContent: "space-between",
                          fontSize: "0.8rem",
                          marginBottom: "0.25rem",
                        }}
                      >
                        <span className="mono" style={{ fontWeight: 600 }}>
                          {pt.date}
                        </span>
                        <span>
                          <strong>{pt.acknowledged}</strong> / {pt.submitted} acknowledged ({pt.completion_rate}%)
                          {pt.draft > 0 ? ` • ${pt.draft} draft(s)` : ""}
                        </span>
                      </div>
                      <div
                        style={{
                          height: "10px",
                          borderRadius: "999px",
                          backgroundColor: "var(--slate-100)",
                          overflow: "hidden",
                        }}
                      >
                        <div
                          style={{
                            width: `${Math.min(100, Math.max(pt.submitted > 0 ? 6 : 0, pt.completion_rate))}%`,
                            height: "100%",
                            backgroundColor:
                              pt.completion_rate === 100
                                ? "var(--green-600)"
                                : "var(--teal-600)",
                          }}
                        />
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Recent Handover Reports & Outstanding Tasks */}
          <div className="grid-2" style={{ marginBottom: "1.5rem" }}>
            <div className="card">
              <div className="card-header">
                <h2 className="card-title">Recent Handover Reports</h2>
                <Link to="/handovers/history" className="btn btn-secondary btn-sm">
                  View All History
                </Link>
              </div>
              {!data?.recent_handovers?.length ? (
                <p style={{ fontSize: "0.875rem", color: "var(--slate-500)" }}>
                  No handover reports found.
                </p>
              ) : (
                <div className="table-wrap">
                  <table className="data-table">
                    <thead>
                      <tr>
                        <th>Code</th>
                        <th>Shift</th>
                        <th>Outgoing → Incoming</th>
                        <th>Status</th>
                        <th>Action</th>
                      </tr>
                    </thead>
                    <tbody>
                      {data.recent_handovers.map((h: any) => (
                        <tr key={h.id}>
                          <td className="mono" style={{ fontWeight: 600 }}>
                            {h.report_code}
                          </td>
                          <td>
                            <div style={{ fontWeight: 500 }}>{h.shift_details?.name}</div>
                            <div style={{ fontSize: "0.75rem", color: "var(--slate-500)" }}>
                              {h.shift_details?.shift_date}
                            </div>
                          </td>
                          <td style={{ fontSize: "0.8rem" }}>
                            <div>Out: {h.submitting_worker_name}</div>
                            <div>In: {h.designated_incoming_worker_name}</div>
                          </td>
                          <td>
                            <HandoverStatusBadge status={h.status} />
                          </td>
                          <td>
                            {h.status === "DRAFT" &&
                            (h.submitting_worker === user?.id || user?.role === "ADMIN") ? (
                              <Link
                                to={`/handovers/${h.id}/edit`}
                                className="btn btn-secondary btn-sm"
                              >
                                Edit Draft
                              </Link>
                            ) : h.status === "SUBMITTED" &&
                              (h.designated_incoming_worker === user?.id ||
                                user?.role === "ADMIN") ? (
                              <Link
                                to={`/handovers/${h.id}/acknowledge`}
                                className="btn btn-primary btn-sm"
                              >
                                Review & Ack
                              </Link>
                            ) : (
                              <Link
                                to={`/handovers/${h.id}`}
                                className="btn btn-secondary btn-sm"
                              >
                                Inspect
                              </Link>
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>

            <div className="card">
              <div className="card-header">
                <h2 className="card-title">Outstanding & Carried-Forward Tasks</h2>
                <Link to="/tasks" className="btn btn-secondary btn-sm">
                  Open Task Tracker
                </Link>
              </div>
              {!data?.outstanding_tasks?.length ? (
                <p style={{ fontSize: "0.875rem", color: "var(--slate-500)" }}>
                  All recorded shift tasks are completed.
                </p>
              ) : (
                <div className="table-wrap">
                  <table className="data-table">
                    <thead>
                      <tr>
                        <th>Task Description</th>
                        <th>Category</th>
                        <th>Priority</th>
                        <th>Status</th>
                      </tr>
                    </thead>
                    <tbody>
                      {data.outstanding_tasks.map((tk: any) => (
                        <tr key={tk.id}>
                          <td>
                            <div style={{ fontWeight: 500 }}>{tk.description}</div>
                            {tk.is_carried_forward && (
                              <span
                                className="badge badge-amber"
                                style={{ marginTop: "0.25rem", fontSize: "0.68rem" }}
                              >
                                Carried Forward
                              </span>
                            )}
                          </td>
                          <td>{tk.category}</td>
                          <td>
                            <PriorityBadge priority={tk.priority} />
                          </td>
                          <td>
                            <TaskStatusBadge status={tk.status} />
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          </div>

          {/* Upcoming/Active Shifts & Recent Notifications */}
          <div className="grid-2">
            <div className="card">
              <div className="card-header">
                <h2 className="card-title">Active & Upcoming Shifts</h2>
                <Link to="/shifts" className="btn btn-secondary btn-sm">
                  All Shifts
                </Link>
              </div>
              {!data?.upcoming_and_active_shifts?.length ? (
                <p style={{ fontSize: "0.875rem", color: "var(--slate-500)" }}>
                  No active or scheduled shifts found.
                </p>
              ) : (
                <div className="table-wrap">
                  <table className="data-table">
                    <thead>
                      <tr>
                        <th>Shift</th>
                        <th>Date & Window</th>
                        <th>Outgoing → Incoming</th>
                        <th>Status</th>
                      </tr>
                    </thead>
                    <tbody>
                      {data.upcoming_and_active_shifts.map((s: any) => (
                        <tr key={s.id}>
                          <td style={{ fontWeight: 600 }}>{s.name}</td>
                          <td className="mono" style={{ fontSize: "0.78rem" }}>
                            {s.shift_date} ({s.start_time.slice(0, 5)}–{s.end_time.slice(0, 5)})
                          </td>
                          <td style={{ fontSize: "0.8rem" }}>
                            {s.outgoing_worker_name} → {s.incoming_worker_name}
                          </td>
                          <td>
                            <span
                              className={`badge ${
                                s.status === "ACTIVE" ? "badge-green" : "badge-teal"
                              }`}
                            >
                              {s.status_display}
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>

            <div className="card">
              <div className="card-header">
                <h2 className="card-title">Recent System Notifications</h2>
                <Link to="/notifications" className="btn btn-secondary btn-sm">
                  Notifications Centre
                </Link>
              </div>
              {!data?.recent_notifications?.length ? (
                <p style={{ fontSize: "0.875rem", color: "var(--slate-500)" }}>
                  No recent notifications for your account.
                </p>
              ) : (
                <div style={{ display: "flex", flexDirection: "column", gap: "0.6rem" }}>
                  {data.recent_notifications.map((n: any) => (
                    <div
                      key={n.id}
                      style={{
                        padding: "0.7rem 0.85rem",
                        borderRadius: "8px",
                        backgroundColor: n.is_read ? "var(--slate-50)" : "var(--teal-50)",
                        border: `1px solid ${n.is_read ? "var(--slate-200)" : "#99f6e4"}`,
                      }}
                    >
                      <div style={{ display: "flex", justifyContent: "space-between", fontSize: "0.82rem", fontWeight: 600 }}>
                        <span>{n.title}</span>
                        <span style={{ fontSize: "0.72rem", color: "var(--slate-500)" }}>
                          {new Date(n.created_at).toLocaleString()}
                        </span>
                      </div>
                      <p style={{ fontSize: "0.8rem", color: "var(--slate-600)", marginTop: "0.2rem" }}>
                        {n.message}
                      </p>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </>
      )}
    </div>
  );
};

export const UserProfilePage: React.FC = () => {
  const { user, organisation, refreshProfile } = useAuth();
  const [fullName, setFullName] = useState(user?.full_name || "");
  const [department, setDepartment] = useState(user?.department || "");
  const [phone, setPhone] = useState(user?.phone_number || "");
  const [empId, setEmpId] = useState(user?.employee_id || "");
  const [profileMsg, setProfileMsg] = useState<string | null>(null);
  const [profileErr, setProfileErr] = useState<string | null>(null);

  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [pwMsg, setPwMsg] = useState<string | null>(null);
  const [pwErr, setPwErr] = useState<string | null>(null);

  const handleSaveProfile = async (e: React.FormEvent) => {
    e.preventDefault();
    setProfileMsg(null);
    setProfileErr(null);
    try {
      await apiClient.patch("/auth/me/", {
        full_name: fullName,
        department,
        phone_number: phone,
        employee_id: empId,
      });
      await refreshProfile();
      setProfileMsg("Profile settings saved successfully.");
    } catch (err: any) {
      setProfileErr(err.response?.data?.detail || "Failed to update profile.");
    }
  };

  const handleChangePassword = async (e: React.FormEvent) => {
    e.preventDefault();
    setPwMsg(null);
    setPwErr(null);
    try {
      const res = await apiClient.post("/auth/change-password/", {
        current_password: currentPassword,
        new_password: newPassword,
      });
      setPwMsg(res.data.detail);
      setCurrentPassword("");
      setNewPassword("");
    } catch (err: any) {
      const d = err.response?.data;
      setPwErr(
        d?.detail ||
          d?.current_password?.[0] ||
          d?.new_password?.[0] ||
          "Password update failed."
      );
    }
  };

  return (
    <div>
      <div style={{ marginBottom: "1.25rem" }}>
        <h1 style={{ fontSize: "1.4rem", fontWeight: 700 }}>
          User Profile & Account Settings
        </h1>
        <p style={{ fontSize: "0.85rem", color: "var(--slate-500)" }}>
          Manage your operational identity, contact details, and authentication security
        </p>
      </div>

      <div className="grid-2">
        <div className="card">
          <h2 className="card-title" style={{ marginBottom: "1rem" }}>
            Operational Identity
          </h2>
          {profileMsg && (
            <div className="alert alert-success">
              <CheckCircle2 size={16} />
              <span>{profileMsg}</span>
            </div>
          )}
          {profileErr && (
            <div className="alert alert-error">
              <AlertTriangle size={16} />
              <span>{profileErr}</span>
            </div>
          )}

          <form onSubmit={handleSaveProfile}>
            <div className="form-group">
              <label className="form-label">Work Email (Read-only Login ID)</label>
              <input
                type="email"
                className="form-control"
                value={user?.email || ""}
                disabled
              />
            </div>
            <div className="form-group">
              <label className="form-label">Assigned Role & Organisation</label>
              <input
                type="text"
                className="form-control"
                value={`${user?.role_display} — ${organisation?.name || ""}`}
                disabled
              />
            </div>
            <div className="form-group">
              <label htmlFor="prof-name" className="form-label">
                Full Name
              </label>
              <input
                id="prof-name"
                type="text"
                className="form-control"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                required
              />
            </div>
            <div className="form-group">
              <label htmlFor="prof-dept" className="form-label">
                Department
              </label>
              <input
                id="prof-dept"
                type="text"
                className="form-control"
                value={department}
                onChange={(e) => setDepartment(e.target.value)}
              />
            </div>
            <div className="grid-2">
              <div className="form-group">
                <label htmlFor="prof-empid" className="form-label">
                  Employee / Badge ID
                </label>
                <input
                  id="prof-empid"
                  type="text"
                  className="form-control mono"
                  value={empId}
                  onChange={(e) => setEmpId(e.target.value)}
                />
              </div>
              <div className="form-group">
                <label htmlFor="prof-phone" className="form-label">
                  Phone Number
                </label>
                <input
                  id="prof-phone"
                  type="text"
                  className="form-control"
                  value={phone}
                  onChange={(e) => setPhone(e.target.value)}
                />
              </div>
            </div>
            <button type="submit" className="btn btn-primary">
              Save Profile Changes
            </button>
          </form>
        </div>

        <div className="card">
          <h2 className="card-title" style={{ marginBottom: "1rem" }}>
            Change Password
          </h2>
          {pwMsg && (
            <div className="alert alert-success">
              <CheckCircle2 size={16} />
              <span>{pwMsg}</span>
            </div>
          )}
          {pwErr && (
            <div className="alert alert-error">
              <AlertTriangle size={16} />
              <span>{pwErr}</span>
            </div>
          )}
          <form onSubmit={handleChangePassword}>
            <div className="form-group">
              <label htmlFor="cur-pw" className="form-label">
                Current Password
              </label>
              <input
                id="cur-pw"
                type="password"
                className="form-control"
                value={currentPassword}
                onChange={(e) => setCurrentPassword(e.target.value)}
                required
              />
            </div>
            <div className="form-group">
              <label htmlFor="new-pw" className="form-label">
                New Password (min 8 chars)
              </label>
              <input
                id="new-pw"
                type="password"
                className="form-control"
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                required
                minLength={8}
              />
            </div>
            <button type="submit" className="btn btn-navy">
              Update Password
            </button>
          </form>
        </div>
      </div>
    </div>
  );
};

export const NotificationsCentrePage: React.FC = () => {
  const [notifications, setNotifications] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [unreadOnly, setUnreadOnly] = useState(false);

  const loadNotifications = async () => {
    setLoading(true);
    try {
      const params: Record<string, string> = {};
      if (unreadOnly) params.is_read = "false";
      const res = await apiClient.get("/notifications/", { params });
      setNotifications(res.data.results || res.data || []);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadNotifications();
  }, [unreadOnly]);

  const handleMarkRead = async (id: string) => {
    await apiClient.post(`/notifications/${id}/mark-read/`, {});
    loadNotifications();
  };

  const handleMarkAllRead = async () => {
    await apiClient.post("/notifications/mark-all-read/", {});
    loadNotifications();
  };

  return (
    <div>
      <div className="card-header" style={{ marginBottom: "1.25rem" }}>
        <div>
          <h1 style={{ fontSize: "1.4rem", fontWeight: 700 }}>
            Notifications Centre
          </h1>
          <p style={{ fontSize: "0.85rem", color: "var(--slate-500)" }}>
            Persistent in-app alerts for handover submissions, acknowledgments, and critical tasks
          </p>
        </div>
        <div style={{ display: "flex", gap: "0.6rem" }}>
          <button
            type="button"
            className={`btn btn-sm ${unreadOnly ? "btn-primary" : "btn-secondary"}`}
            onClick={() => setUnreadOnly(!unreadOnly)}
          >
            <Filter size={14} />
            <span>{unreadOnly ? "Showing Unread Only" : "Filter Unread Only"}</span>
          </button>
          <button
            type="button"
            className="btn btn-secondary btn-sm"
            onClick={handleMarkAllRead}
            data-testid="mark-all-read-btn"
          >
            <CheckCheck size={15} />
            <span>Mark All as Read</span>
          </button>
        </div>
      </div>

      <div className="card">
        {loading ? (
          <p style={{ padding: "2rem", textAlign: "center", color: "var(--slate-500)" }}>
            Loading notifications...
          </p>
        ) : notifications.length === 0 ? (
          <div style={{ padding: "2.5rem", textAlign: "center", color: "var(--slate-500)" }}>
            <Bell size={28} style={{ marginBottom: "0.5rem", opacity: 0.5 }} />
            <p>No notifications match your current filter.</p>
          </div>
        ) : (
          <div style={{ display: "flex", flexDirection: "column", gap: "0.75rem" }}>
            {notifications.map((n) => (
              <div
                key={n.id}
                style={{
                  padding: "1rem",
                  borderRadius: "8px",
                  backgroundColor: n.is_read ? "#fff" : "var(--teal-50)",
                  border: `1px solid ${n.is_read ? "var(--slate-200)" : "#5eead4"}`,
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "flex-start",
                  gap: "1rem",
                }}
              >
                <div>
                  <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", marginBottom: "0.25rem" }}>
                    <span
                      className={`badge ${
                        n.notification_type === "CRITICAL_TASK"
                          ? "badge-red"
                          : n.notification_type === "HANDOVER_ACKNOWLEDGED"
                          ? "badge-green"
                          : "badge-teal"
                      }`}
                    >
                      {n.type_display}
                    </span>
                    <strong style={{ fontSize: "0.95rem" }}>{n.title}</strong>
                    {!n.is_read && (
                      <span className="badge badge-amber" style={{ fontSize: "0.68rem" }}>
                        Unread
                      </span>
                    )}
                  </div>
                  <p style={{ fontSize: "0.875rem", color: "var(--slate-600)", marginBottom: "0.35rem" }}>
                    {n.message}
                  </p>
                  <div style={{ fontSize: "0.75rem", color: "var(--slate-500)" }}>
                    Recorded: {new Date(n.created_at).toLocaleString()}
                  </div>
                </div>

                <div style={{ display: "flex", gap: "0.5rem", flexShrink: 0 }}>
                  {n.related_handover && (
                    <Link
                      to={`/handovers/${n.related_handover}`}
                      className="btn btn-secondary btn-sm"
                    >
                      Open {n.handover_code || "Handover"}
                    </Link>
                  )}
                  {!n.is_read && (
                    <button
                      type="button"
                      className="btn btn-primary btn-sm"
                      onClick={() => handleMarkRead(n.id)}
                    >
                      Mark Read
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export const HandoverHistoryPage: React.FC = () => {
  const { user } = useAuth();
  const [handovers, setHandovers] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState("");
  const [priorityFilter, setPriorityFilter] = useState("");
  const [searchQuery, setSearchQuery] = useState("");
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");

  const fetchHandovers = async () => {
    setLoading(true);
    try {
      const params: Record<string, string> = {};
      if (statusFilter) params.status = statusFilter;
      if (priorityFilter) params.priority = priorityFilter;
      if (searchQuery.trim()) params.search = searchQuery.trim();
      if (dateFrom) params.date_from = dateFrom;
      if (dateTo) params.date_to = dateTo;
      const res = await apiClient.get("/handovers/", { params });
      setHandovers(res.data.results || res.data || []);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHandovers();
  }, [statusFilter, priorityFilter, dateFrom, dateTo]);

  return (
    <div>
      <div className="card-header" style={{ marginBottom: "1.25rem" }}>
        <div>
          <h1 style={{ fontSize: "1.4rem", fontWeight: 700 }}>
            Handover History & Audit Registry
          </h1>
          <p style={{ fontSize: "0.85rem", color: "var(--slate-500)" }}>
            Inspect submitted, acknowledged, and draft shift handover reports and their acknowledgment timestamps
          </p>
        </div>
        {(user?.role === "OUTGOING_WORKER" || user?.role === "ADMIN") && (
          <Link to="/handovers/create" className="btn btn-primary btn-sm">
            <FilePlus2 size={15} />
            <span>Create Handover Report</span>
          </Link>
        )}
      </div>

      <div className="card" style={{ marginBottom: "1.25rem" }}>
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(170px, 1fr))",
            gap: "0.75rem",
            alignItems: "end",
          }}
        >
          <div>
            <label className="form-label">Search Code / Worker / Notes</label>
            <div style={{ display: "flex", gap: "0.35rem" }}>
              <input
                type="text"
                className="form-control"
                placeholder="e.g., HND-DEMO or Ochieng"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
              />
              <button
                type="button"
                className="btn btn-secondary"
                onClick={fetchHandovers}
                aria-label="Search"
              >
                <Search size={15} />
              </button>
            </div>
          </div>

          <div>
            <label className="form-label">Handover Status</label>
            <select
              className="form-control"
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
            >
              <option value="">All Statuses</option>
              <option value="DRAFT">Draft</option>
              <option value="SUBMITTED">Submitted (Awaiting Ack)</option>
              <option value="ACKNOWLEDGED">Acknowledged</option>
            </select>
          </div>

          <div>
            <label className="form-label">Contains Task Priority</label>
            <select
              className="form-control"
              value={priorityFilter}
              onChange={(e) => setPriorityFilter(e.target.value)}
            >
              <option value="">Any Priority</option>
              <option value="Critical">Critical</option>
              <option value="High">High</option>
              <option value="Medium">Medium</option>
              <option value="Low">Low</option>
            </select>
          </div>

          <div>
            <label className="form-label">From Shift Date</label>
            <input
              type="date"
              className="form-control"
              value={dateFrom}
              onChange={(e) => setDateFrom(e.target.value)}
            />
          </div>

          <div>
            <label className="form-label">To Shift Date</label>
            <input
              type="date"
              className="form-control"
              value={dateTo}
              onChange={(e) => setDateTo(e.target.value)}
            />
          </div>
        </div>
      </div>

      <div className="card">
        {loading ? (
          <p style={{ padding: "2rem", textAlign: "center" }}>
            Loading handover records...
          </p>
        ) : handovers.length === 0 ? (
          <p style={{ padding: "2rem", textAlign: "center", color: "var(--slate-500)" }}>
            No handover reports match the selected filters.
          </p>
        ) : (
          <div className="table-wrap">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Report Code</th>
                  <th>Shift & Date</th>
                  <th>Outgoing Worker</th>
                  <th>Designated Incoming</th>
                  <th>Tasks (Unresolved)</th>
                  <th>Equipment</th>
                  <th>Status</th>
                  <th>Submitted / Acknowledged</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {handovers.map((h) => (
                  <tr key={h.id}>
                    <td className="mono" style={{ fontWeight: 700 }}>
                      {h.report_code}
                    </td>
                    <td>
                      <div style={{ fontWeight: 600 }}>{h.shift_details?.name}</div>
                      <div style={{ fontSize: "0.75rem", color: "var(--slate-500)" }}>
                        {h.shift_details?.shift_date}
                      </div>
                    </td>
                    <td>{h.submitting_worker_name}</td>
                    <td>{h.designated_incoming_worker_name}</td>
                    <td>
                      <strong>{h.total_tasks}</strong> total ({h.unresolved_tasks} unresolved
                      {h.critical_tasks > 0 ? `, ${h.critical_tasks} critical` : ""})
                    </td>
                    <td>
                      <EquipmentStatusBadge status={h.equipment_status} />
                    </td>
                    <td>
                      <HandoverStatusBadge status={h.status} />
                    </td>
                    <td style={{ fontSize: "0.76rem", color: "var(--slate-600)" }}>
                      <div>
                        Sub:{" "}
                        {h.submitted_at
                          ? new Date(h.submitted_at).toLocaleString()
                          : "—"}
                      </div>
                      <div>
                        Ack:{" "}
                        {h.acknowledged_at
                          ? `${new Date(h.acknowledged_at).toLocaleString()} (${h.acknowledged_by_name})`
                          : "Pending"}
                      </div>
                    </td>
                    <td>
                      <div style={{ display: "flex", gap: "0.4rem" }}>
                        <Link
                          to={`/handovers/${h.id}`}
                          className="btn btn-secondary btn-sm"
                        >
                          Details
                        </Link>
                        {h.status === "DRAFT" &&
                          (h.submitting_worker === user?.id ||
                            user?.role === "ADMIN") && (
                            <Link
                              to={`/handovers/${h.id}/edit`}
                              className="btn btn-primary btn-sm"
                            >
                              Edit
                            </Link>
                          )}
                        {h.status === "SUBMITTED" &&
                          (h.designated_incoming_worker === user?.id ||
                            user?.role === "ADMIN") && (
                            <Link
                              to={`/handovers/${h.id}/acknowledge`}
                              className="btn btn-primary btn-sm"
                            >
                              Acknowledge
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
