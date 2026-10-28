import React from "react";
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { AuthProvider } from "./context/AuthContext";
import { AppLayout, ProtectedRoute } from "./components/Layout";
import {
  AccessDeniedPage,
  LoginPage,
  NotFoundPage,
  PasswordRecoveryPage,
} from "./pages/PublicAuthPages";
import {
  DashboardOverviewPage,
  HandoverHistoryPage,
  NotificationsCentrePage,
  UserProfilePage,
} from "./pages/SharedPages";
import {
  CreateEditHandoverPage,
  HandoverReportDetailsPage,
  IncomingHandoverAcknowledgePage,
  LogShiftActivityPage,
  ShiftManagementPage,
  TaskTrackingPage,
} from "./pages/OperationalPages";
import {
  HandoverAnalyticsPage,
  SupervisorDashboardPage,
} from "./pages/SupervisoryPages";
import {
  CreateEditShiftPage,
  CreateEditUserPage,
  SystemConfigurationPage,
  UserManagementPage,
} from "./pages/AdminPages";

export const AppRoutes: React.FC = () => {
  return (
    <Routes>
      {/* 1-4: Public & Authentication Pages */}
      <Route path="/login" element={<LoginPage />} />
      <Route path="/forgot-password" element={<PasswordRecoveryPage />} />
      <Route path="/reset-password" element={<PasswordRecoveryPage />} />

      {/* Authenticated Shell */}
      <Route element={<ProtectedRoute />}>
        <Route element={<AppLayout />}>
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
          <Route path="/access-denied" element={<AccessDeniedPage />} />

          {/* 5-8: Shared Application Pages */}
          <Route path="/dashboard" element={<DashboardOverviewPage />} />
          <Route path="/profile" element={<UserProfilePage />} />
          <Route path="/notifications" element={<NotificationsCentrePage />} />
          <Route path="/handovers/history" element={<HandoverHistoryPage />} />

          {/* 9-14: Operational Pages */}
          <Route path="/shifts" element={<ShiftManagementPage />} />
          <Route
            path="/handovers/create"
            element={
              <ProtectedRoute allowedRoles={["OUTGOING_WORKER", "ADMIN"]}>
                <CreateEditHandoverPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/handovers/:id/edit"
            element={
              <ProtectedRoute allowedRoles={["OUTGOING_WORKER", "ADMIN"]}>
                <CreateEditHandoverPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/activity/log"
            element={
              <ProtectedRoute allowedRoles={["OUTGOING_WORKER", "ADMIN"]}>
                <LogShiftActivityPage />
              </ProtectedRoute>
            }
          />
          <Route path="/tasks" element={<TaskTrackingPage />} />
          <Route path="/handovers/incoming" element={<IncomingHandoverAcknowledgePage />} />
          <Route path="/handovers/:id/acknowledge" element={<IncomingHandoverAcknowledgePage />} />
          <Route path="/handovers/:id" element={<HandoverReportDetailsPage />} />

          {/* 15-17: Supervisory Pages */}
          <Route
            path="/supervisor/dashboard"
            element={
              <ProtectedRoute allowedRoles={["SUPERVISOR", "ADMIN"]}>
                <SupervisorDashboardPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/supervisor/analytics"
            element={
              <ProtectedRoute allowedRoles={["SUPERVISOR", "ADMIN"]}>
                <HandoverAnalyticsPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/supervisor/history/:id"
            element={
              <ProtectedRoute allowedRoles={["SUPERVISOR", "ADMIN"]}>
                <HandoverReportDetailsPage />
              </ProtectedRoute>
            }
          />

          {/* 18-21: Administrative Pages */}
          <Route
            path="/admin/users"
            element={
              <ProtectedRoute allowedRoles={["ADMIN"]}>
                <UserManagementPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/admin/users/new"
            element={
              <ProtectedRoute allowedRoles={["ADMIN"]}>
                <CreateEditUserPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/admin/users/:id/edit"
            element={
              <ProtectedRoute allowedRoles={["ADMIN"]}>
                <CreateEditUserPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/admin/shifts/new"
            element={
              <ProtectedRoute allowedRoles={["ADMIN"]}>
                <CreateEditShiftPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/admin/shifts/:id/edit"
            element={
              <ProtectedRoute allowedRoles={["ADMIN"]}>
                <CreateEditShiftPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/admin/configuration"
            element={
              <ProtectedRoute allowedRoles={["ADMIN"]}>
                <SystemConfigurationPage />
              </ProtectedRoute>
            }
          />

          <Route path="/404" element={<NotFoundPage />} />
          <Route path="*" element={<NotFoundPage />} />
        </Route>
      </Route>
    </Routes>
  );
};

export const App: React.FC = () => {
  return (
    <AuthProvider>
      <BrowserRouter>
        <AppRoutes />
      </BrowserRouter>
    </AuthProvider>
  );
};

export default App;
