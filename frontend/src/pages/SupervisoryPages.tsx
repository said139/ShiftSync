import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  BarChart3,
  BrainCircuit,
  Clock,
  Download,
  FileSpreadsheet,
  Filter,
  Shield,
} from "lucide-react";
import { apiClient } from "../api/client";
import { DashboardOverviewPage } from "./SharedPages";
import { HandoverStatusBadge, PriorityBadge } from "../components/Badges";

/* ============================================================================
   PAGE 15: SUPERVISOR DASHBOARD (/supervisor/dashboard)
   ============================================================================ */
export const SupervisorDashboardPage: React.FC = () => {
  return (
    <DashboardOverviewPage
      forcedScope="organisation"
      titleOverride="Supervisor Organisation-Wide Oversight Dashboard"
    />
  );
};

/* ============================================================================
   PAGE 16: HANDOVER ANALYTICS & BASIC REPORTS (/supervisor/analytics)
   ============================================================================ */
export const HandoverAnalyticsPage: React.FC = () => {
  const [reportData, setReportData] = useState<any | null>(null);
  const [shifts, setShifts] = useState<any[]>([]);
  const [workers, setWorkers] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [shiftFilter, setShiftFilter] = useState("");
  const [workerFilter, setWorkerFilter] = useState("");
  const [priorityFilter, setPriorityFilter] = useState("");

  useEffect(() => {
    Promise.all([
      apiClient.get("/shifts/"),
      apiClient.get("/users/colleagues/"),
    ]).then(([sRes, uRes]) => {
      setShifts(sRes.data.results || sRes.data || []);
      setWorkers(uRes.data || []);
    });
  }, []);

  const loadAnalytics = async () => {
    setLoading(true);
    try {
      const params: Record<string, string> = {};
      if (dateFrom) params.date_from = dateFrom;
      if (dateTo) params.date_to = dateTo;
      if (statusFilter) params.status = statusFilter;
      if (shiftFilter) params.shift = shiftFilter;
      if (workerFilter) params.worker = workerFilter;
      if (priorityFilter) params.priority = priorityFilter;
      const res = await apiClient.get("/analytics/supervisor-report/", {
        params,
      });
      setReportData(res.data);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAnalytics();
  }, [dateFrom, dateTo, statusFilter, shiftFilter, workerFilter, priorityFilter]);

  const handleExportCSV = async () => {
    const params: Record<string, string> = {};
    if (dateFrom) params.date_from = dateFrom;
    if (dateTo) params.date_to = dateTo;
    if (statusFilter) params.status = statusFilter;
    const res = await apiClient.get("/analytics/export-csv/", {
      params,
      responseType: "blob",
    });
    const url = window.URL.createObjectURL(new Blob([res.data]));
    const link = document.createElement("a");
    link.href = url;
    link.setAttribute("download", "shiftsync_handover_performance_report.csv");
    document.body.appendChild(link);
    link.click();
    link.remove();
  };

  const nlpStats = reportData?.nlp_statistics || {};

  return (
    <div>
      <div className="card-header" style={{ marginBottom: "1.25rem" }}>
        <div>
          <h1 style={{ fontSize: "1.4rem", fontWeight: 700 }}>
            Handover Analytics & Supervisory Performance Reports
          </h1>
          <p style={{ fontSize: "0.85rem", color: "var(--slate-500)" }}>
            Filter operational records by date, shift, status, worker, and priority, and export CSV audit reports
          </p>
        </div>

        <button
          type="button"
          className="btn btn-primary"
          onClick={handleExportCSV}
          data-testid="export-csv-report-btn"
        >
          <Download size={16} />
          <span>Export CSV Performance Report</span>
        </button>
      </div>

      {/* Filters Card */}
      <div className="card" style={{ marginBottom: "1.25rem" }}>
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(170px, 1fr))",
            gap: "0.75rem",
          }}
        >
          <div>
            <label className="form-label">From Date</label>
            <input
              type="date"
              className="form-control"
              value={dateFrom}
              onChange={(e) => setDateFrom(e.target.value)}
            />
          </div>
          <div>
            <label className="form-label">To Date</label>
            <input
              type="date"
              className="form-control"
              value={dateTo}
              onChange={(e) => setDateTo(e.target.value)}
            />
          </div>
          <div>
            <label className="form-label">Shift</label>
            <select
              className="form-control"
              value={shiftFilter}
              onChange={(e) => setShiftFilter(e.target.value)}
            >
              <option value="">All Shifts</option>
              {shifts.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.name} ({s.shift_date})
                </option>
              ))}
            </select>
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
              <option value="SUBMITTED">Submitted (Pending Ack)</option>
              <option value="ACKNOWLEDGED">Acknowledged</option>
            </select>
          </div>
          <div>
            <label className="form-label">Worker</label>
            <select
              className="form-control"
              value={workerFilter}
              onChange={(e) => setWorkerFilter(e.target.value)}
            >
              <option value="">All Workers</option>
              {workers.map((w) => (
                <option key={w.id} value={w.id}>
                  {w.full_name} ({w.role_display})
                </option>
              ))}
            </select>
          </div>
          <div>
            <label className="form-label">Task Priority</label>
            <select
              className="form-control"
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
      </div>

      {loading && !reportData ? (
        <div className="card" style={{ padding: "2rem", textAlign: "center" }}>
          Generating supervisory analytics...
        </div>
      ) : (
        <>
          <div className="metrics-grid">
            <div className="metric-card">
              <span className="metric-label">Total Handovers Matched</span>
              <span className="metric-value">{reportData?.total_handovers ?? 0}</span>
              <span className="metric-sub">
                {reportData?.acknowledged_count ?? 0} acknowledged •{" "}
                {reportData?.submitted_count ?? 0} awaiting ack
              </span>
            </div>

            <div className="metric-card green">
              <span className="metric-label">Avg Acknowledgment Time</span>
              <span className="metric-value">
                {reportData?.average_acknowledgment_minutes ?? 0} min
              </span>
              <span className="metric-sub">
                Mean turnaround from submission to sign-off
              </span>
            </div>

            <div className="metric-card navy">
              <span className="metric-label">NLP-Assisted Tasks</span>
              <span className="metric-value">
                {nlpStats.total_nlp_assisted_tasks ?? 0}
              </span>
              <span className="metric-sub">
                {nlpStats.manually_overridden ?? 0} manual overrides recorded
              </span>
            </div>

            <div className="metric-card">
              <span className="metric-label">NLP Suggestion Acceptance</span>
              <span className="metric-value">
                {nlpStats.acceptance_rate_percent ?? 100}%
              </span>
              <span className="metric-sub">
                {nlpStats.accepted_without_override ?? 0} accepted without change
              </span>
            </div>
          </div>

          <div className="grid-2" style={{ marginBottom: "1.25rem" }}>
            <div className="card">
              <h2 className="card-title" style={{ marginBottom: "0.75rem" }}>
                Task Category Performance Breakdown
              </h2>
              <div className="table-wrap">
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>Category</th>
                      <th>Total Tasks</th>
                      <th>Completed</th>
                      <th>Unresolved</th>
                      <th>Critical</th>
                    </tr>
                  </thead>
                  <tbody>
                    {(reportData?.category_breakdown || []).map((row: any) => (
                      <tr key={row.category}>
                        <td style={{ fontWeight: 600 }}>{row.category}</td>
                        <td>{row.total}</td>
                        <td style={{ color: "var(--green-700)", fontWeight: 600 }}>
                          {row.completed}
                        </td>
                        <td style={{ color: "var(--amber-700)", fontWeight: 600 }}>
                          {row.unresolved}
                        </td>
                        <td style={{ color: "var(--red-700)", fontWeight: 600 }}>
                          {row.critical}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            <div className="card">
              <h2 className="card-title" style={{ marginBottom: "0.75rem" }}>
                Task Priority Distribution
              </h2>
              <div className="table-wrap">
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>Priority Level</th>
                      <th>Total Tasks</th>
                      <th>Completed</th>
                      <th>Unresolved</th>
                    </tr>
                  </thead>
                  <tbody>
                    {(reportData?.priority_breakdown || []).map((row: any) => (
                      <tr key={row.priority}>
                        <td>
                          <PriorityBadge priority={row.priority} />
                        </td>
                        <td style={{ fontWeight: 600 }}>{row.total}</td>
                        <td>{row.completed}</td>
                        <td>{row.unresolved}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>

          <div className="card">
            <h2 className="card-title" style={{ marginBottom: "0.85rem" }}>
              Filtered Handover Performance Records ({reportData?.handovers?.length || 0})
            </h2>
            <div className="table-wrap">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Report Code</th>
                    <th>Shift & Date</th>
                    <th>Outgoing → Incoming</th>
                    <th>Tasks (Unresolved)</th>
                    <th>Status</th>
                    <th>Submitted / Acknowledged</th>
                    <th>Inspect</th>
                  </tr>
                </thead>
                <tbody>
                  {(reportData?.handovers || []).map((h: any) => (
                    <tr key={h.id}>
                      <td className="mono" style={{ fontWeight: 700 }}>
                        {h.report_code}
                      </td>
                      <td>
                        <div>{h.shift_details?.name}</div>
                        <div style={{ fontSize: "0.75rem", color: "var(--slate-500)" }}>
                          {h.shift_details?.shift_date}
                        </div>
                      </td>
                      <td style={{ fontSize: "0.8rem" }}>
                        {h.submitting_worker_name} → {h.designated_incoming_worker_name}
                      </td>
                      <td>
                        {h.total_tasks} ({h.unresolved_tasks} unresolved)
                      </td>
                      <td>
                        <HandoverStatusBadge status={h.status} />
                      </td>
                      <td style={{ fontSize: "0.75rem" }}>
                        <div>
                          Sub:{" "}
                          {h.submitted_at
                            ? new Date(h.submitted_at).toLocaleString()
                            : "—"}
                        </div>
                        <div>
                          Ack:{" "}
                          {h.acknowledged_at
                            ? new Date(h.acknowledged_at).toLocaleString()
                            : "Pending"}
                        </div>
                      </td>
                      <td>
                        <Link
                          to={`/supervisor/history/${h.id}`}
                          className="btn btn-secondary btn-sm"
                        >
                          Audit View
                        </Link>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </>
      )}
    </div>
  );
};
