import React, { useEffect, useState } from "react";
import { Link, NavLink, Navigate, Outlet, useLocation, useNavigate } from "react-router-dom";
import {
  Activity,
  BarChart3,
  Bell,
  CalendarClock,
  CheckSquare,
  ClipboardCheck,
  FilePlus2,
  History,
  LayoutDashboard,
  LogOut,
  Menu,
  Plane,
  Settings,
  Shield,
  UserCheck,
  UserCog,
  Users,
  X,
} from "lucide-react";
import { useAuth, UserRole } from "../context/AuthContext";
import { apiClient } from "../api/client";

export const ProtectedRoute: React.FC<{
  allowedRoles?: UserRole[];
  children?: React.ReactNode;
}> = ({ allowedRoles, children }) => {
  const { user, loading } = useAuth();
  const location = useLocation();

  if (loading) {
    return (
      <div style={{ padding: "4rem", textAlign: "center", color: "var(--slate-600)" }}>
        Loading ShiftSync session...
      </div>
    );
  }

  if (!user) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  if (allowedRoles && !allowedRoles.includes(user.role)) {
    return <Navigate to="/access-denied" replace />;
  }

  return children ? <>{children}</> : <Outlet />;
};

export const AppLayout: React.FC = () => {
  const { user, organisation, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [unreadCount, setUnreadCount] = useState<number>(0);

  const fetchUnreadCount = async () => {
    if (!user) return;
    try {
      const res = await apiClient.get("/notifications/unread-count/");
      setUnreadCount(res.data?.unread_count ?? 0);
    } catch {
      // Ignore transient polling errors
    }
  };

  useEffect(() => {
    fetchUnreadCount();
    const timer = setInterval(fetchUnreadCount, 15000);
    return () => clearInterval(timer);
  }, [user, location.pathname]);

  useEffect(() => {
    setSidebarOpen(false);
  }, [location.pathname]);

  if (!user) return null;

  const isWorker =
    user.role === "OUTGOING_WORKER" ||
    user.role === "INCOMING_WORKER" ||
    user.role === "ADMIN";
  const isSupervisor = user.role === "SUPERVISOR" || user.role === "ADMIN";
  const isAdmin = user.role === "ADMIN";

  const handleLogout = async () => {
    await logout();
    navigate("/login");
  };

  return (
    <div className="app-shell">
      <div
        className={`sidebar-overlay ${sidebarOpen ? "open" : ""}`}
        onClick={() => setSidebarOpen(false)}
      />

      <aside className={`sidebar ${sidebarOpen ? "open" : ""}`} aria-label="Main Navigation">
        <div className="sidebar-brand">
          <Link to="/dashboard" className="brand-logo">
            <div className="brand-icon">
              <Plane size={20} color="#fff" />
            </div>
            <div>
              <div style={{ fontWeight: 800, fontSize: "1.05rem", letterSpacing: "-0.02em", display: "flex", alignItems: "center", gap: "0.35rem" }}>
                <span>ShiftSync</span>
                <span style={{ fontSize: "0.62rem", padding: "0.1rem 0.35rem", backgroundColor: "var(--kq-red-600)", borderRadius: "3px", color: "#fff", fontWeight: 700 }}>KQ</span>
              </div>
              <div style={{ fontSize: "0.7rem", color: "var(--kq-gold-400)", fontWeight: 600 }}>
                {organisation?.code || "KQ-MRO"} • JKIA
              </div>
            </div>
          </Link>
          <button
            type="button"
            className="mobile-menu-btn"
            style={{ color: "#fff", borderColor: "var(--navy-700)" }}
            onClick={() => setSidebarOpen(false)}
            aria-label="Close Menu"
          >
            <X size={18} />
          </button>
        </div>

        <nav className="sidebar-nav">
          {/* Shared Section */}
          <div>
            <div className="nav-section-title">Overview & Shared</div>
            <NavLink to="/dashboard" className="nav-link">
              <LayoutDashboard size={17} />
              <span>Dashboard Overview</span>
            </NavLink>
            <NavLink to="/notifications" className="nav-link">
              <Bell size={17} />
              <span style={{ flex: 1 }}>Notifications Centre</span>
              {unreadCount > 0 && (
                <span
                  className="badge badge-red"
                  style={{ padding: "0.1rem 0.45rem", fontSize: "0.7rem" }}
                  data-testid="sidebar-unread-badge"
                >
                  {unreadCount}
                </span>
              )}
            </NavLink>
            <NavLink to="/handovers/history" className="nav-link">
              <History size={17} />
              <span>Handover History</span>
            </NavLink>
            <NavLink to="/profile" className="nav-link">
              <UserCog size={17} />
              <span>Profile & Settings</span>
            </NavLink>
          </div>

          {/* Operational Section */}
          <div>
            <div className="nav-section-title">Shift Operations</div>
            <NavLink to="/shifts" className="nav-link">
              <CalendarClock size={17} />
              <span>Shift Management</span>
            </NavLink>
            {isWorker && (
              <>
                <NavLink to="/handovers/create" className="nav-link">
                  <FilePlus2 size={17} />
                  <span>Create Handover Report</span>
                </NavLink>
                <NavLink to="/activity/log" className="nav-link">
                  <Activity size={17} />
                  <span>Log Shift Activity (NLP)</span>
                </NavLink>
                <NavLink to="/handovers/incoming" className="nav-link">
                  <ClipboardCheck size={17} />
                  <span>Incoming Review & Ack</span>
                </NavLink>
              </>
            )}
            <NavLink to="/tasks" className="nav-link">
              <CheckSquare size={17} />
              <span>Task Tracking</span>
            </NavLink>
          </div>

          {/* Supervisory Section */}
          {isSupervisor && (
            <div>
              <div className="nav-section-title">Supervisory Oversight</div>
              <NavLink to="/supervisor/dashboard" className="nav-link">
                <Shield size={17} />
                <span>Supervisor Dashboard</span>
              </NavLink>
              <NavLink to="/supervisor/analytics" className="nav-link">
                <BarChart3 size={17} />
                <span>Handover Analytics & Reports</span>
              </NavLink>
            </div>
          )}

          {/* Administrative Section */}
          {isAdmin && (
            <div>
              <div className="nav-section-title">System Administration</div>
              <NavLink to="/admin/users" className="nav-link">
                <Users size={17} />
                <span>User Management</span>
              </NavLink>
              <NavLink to="/admin/users/new" className="nav-link">
                <UserCheck size={17} />
                <span>Create User Account</span>
              </NavLink>
              <NavLink to="/admin/shifts/new" className="nav-link">
                <CalendarClock size={17} />
                <span>Create & Assign Shift</span>
              </NavLink>
              <NavLink to="/admin/configuration" className="nav-link">
                <Settings size={17} />
                <span>System Configuration</span>
              </NavLink>
            </div>
          )}
        </nav>

        <div className="sidebar-footer">
          <div style={{ fontSize: "0.85rem", fontWeight: 600, color: "#fff" }}>
            {user.full_name}
          </div>
          <div style={{ fontSize: "0.75rem", color: "var(--slate-400)", marginBottom: "0.65rem" }}>
            {user.role_display} • {user.department}
          </div>
          <button
            type="button"
            onClick={handleLogout}
            className="btn btn-secondary btn-sm"
            style={{
              width: "100%",
              backgroundColor: "var(--navy-800)",
              color: "#fff",
              borderColor: "var(--navy-700)",
            }}
            data-testid="logout-button"
          >
            <LogOut size={14} />
            <span>Sign Out</span>
          </button>
        </div>
      </aside>

      <div className="main-area">
        <header className="topbar">
          <div style={{ display: "flex", alignItems: "center", gap: "0.75rem" }}>
            <button
              type="button"
              className="mobile-menu-btn"
              onClick={() => setSidebarOpen(true)}
              aria-label="Open Navigation Menu"
            >
              <Menu size={20} />
            </button>
            <div>
              <span style={{ fontWeight: 600, fontSize: "0.95rem", color: "var(--navy-900)" }}>
                {organisation?.name || "ShiftSync Operations"}
              </span>
              <span
                className="badge badge-teal"
                style={{ marginLeft: "0.65rem", fontSize: "0.7rem" }}
              >
                {user.role_display}
              </span>
            </div>
          </div>

          <div style={{ display: "flex", alignItems: "center", gap: "0.85rem" }}>
            <Link
              to="/notifications"
              className="btn btn-secondary btn-sm"
              aria-label="Notifications"
              data-testid="topbar-notifications-link"
            >
              <Bell size={15} />
              <span>Alerts</span>
              {unreadCount > 0 && (
                <span className="badge badge-red" style={{ padding: "0.05rem 0.45rem" }}>
                  {unreadCount}
                </span>
              )}
            </Link>
            <Link to="/profile" className="btn btn-secondary btn-sm">
              <UserCog size={15} />
              <span>{user.email}</span>
            </Link>
          </div>
        </header>

        <main className="page-content">
          <Outlet />
        </main>
      </div>
    </div>
  );
};
