import React from "react";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, it, expect, vi, beforeEach } from "vitest";
import {
  HandoverStatusBadge,
  PriorityBadge,
  TaskStatusBadge,
  EquipmentStatusBadge,
} from "../components/Badges";
import { AccessDeniedPage, LoginPage, NotFoundPage, SignUpPage } from "../pages/PublicAuthPages";
import { DashboardOverviewPage, NotificationsCentrePage } from "../pages/SharedPages";
import { TaskTrackingPage } from "../pages/OperationalPages";
import { apiClient, getAccessToken, setAccessToken } from "../api/client";

vi.mock("../context/AuthContext", () => ({
  useAuth: () => ({
    user: {
      id: "u-1",
      email: "outgoing@shiftsync.ac.ke",
      full_name: "Eng. David Ochieng",
      role: "OUTGOING_WORKER",
      role_display: "Outgoing Worker",
      department: "Line Maintenance",
    },
    organisation: {
      id: "org-1",
      name: "Kenya Airways Line Maintenance",
      code: "KQ-MRO",
      task_categories: ["Maintenance", "Safety & Compliance", "Equipment Check", "Operations"],
      priority_levels: ["Low", "Medium", "High", "Critical"],
    },
    loading: false,
    login: vi.fn(),
    logout: vi.fn(),
    refreshProfile: vi.fn(),
  }),
}));

describe("ShiftSync Frontend Security, Components, Dashboard, Notifications & Tasks", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it("stores JWT access tokens strictly in memory and never in localStorage", () => {
    localStorage.clear();
    setAccessToken("eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.in-memory-token");
    expect(getAccessToken()).toBe(
      "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.in-memory-token"
    );
    expect(localStorage.length).toBe(0);
    setAccessToken(null);
    expect(getAccessToken()).toBeNull();
  });

  it("renders accessible status and priority badges with text labels alongside icons", () => {
    render(
      <div>
        <HandoverStatusBadge status="ACKNOWLEDGED" />
        <HandoverStatusBadge status="SUBMITTED" />
        <HandoverStatusBadge status="DRAFT" />
        <PriorityBadge priority="Critical" />
        <TaskStatusBadge status="In Progress" />
        <EquipmentStatusBadge status="CRITICAL_FAULT" />
      </div>
    );
    expect(screen.getByText("Acknowledged")).toBeInTheDocument();
    expect(screen.getByText("Submitted (Awaiting Ack)")).toBeInTheDocument();
    expect(screen.getByText("Draft")).toBeInTheDocument();
    expect(screen.getByText("Critical")).toBeInTheDocument();
    expect(screen.getByText("In Progress")).toBeInTheDocument();
    expect(screen.getByText("Critical Fault / Grounded")).toBeInTheDocument();
  });

  it("validates required email and password fields on LoginPage", () => {
    render(
      <MemoryRouter>
        <LoginPage />
      </MemoryRouter>
    );
    const submitBtn = screen.getByTestId("login-submit-button");
    fireEvent.click(submitBtn);
    expect(screen.getByTestId("login-error")).toHaveTextContent(
      "Please enter both your email address and password."
    );
  });

  it("populates demo credentials when quick-fill role buttons are clicked", () => {
    render(
      <MemoryRouter>
        <LoginPage />
      </MemoryRouter>
    );
    fireEvent.click(screen.getByTestId("demo-supervisor-btn"));
    const emailInput = screen.getByTestId("login-email-input") as HTMLInputElement;
    expect(emailInput.value).toBe("supervisor@shiftsync.ac.ke");
  });

  it("renders AccessDeniedPage and NotFoundPage with clear role feedback", () => {
    render(
      <MemoryRouter>
        <AccessDeniedPage />
        <NotFoundPage />
      </MemoryRouter>
    );
    expect(screen.getByText("403 — Access Denied")).toBeInTheDocument();
    expect(screen.getByText("404 — Page Not Found")).toBeInTheDocument();
  });

  it("renders DashboardOverviewPage metric cards from backend API response", async () => {
    vi.spyOn(apiClient, "get").mockResolvedValueOnce({
      data: {
        scope: "personal",
        role: "OUTGOING_WORKER",
        organisation_name: "Kenya Airways Line Maintenance",
        metrics: {
          active_shifts: 2,
          scheduled_shifts: 1,
          handovers_awaiting_acknowledgment: 1,
          submitted_handovers: 3,
          acknowledged_handovers: 2,
          draft_handovers: 1,
          unresolved_tasks: 2,
          carried_forward_tasks: 1,
          critical_priority_tasks: 1,
          handover_completion_rate: 66.7,
          completion_rate_numerator: 2,
          completion_rate_denominator: 3,
        },
        recent_handovers: [],
        outstanding_tasks: [],
        critical_tasks: [],
        safety_and_equipment_alerts: [],
        upcoming_and_active_shifts: [],
        recent_notifications: [],
        completion_trend: [],
      },
    });

    render(
      <MemoryRouter>
        <DashboardOverviewPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByTestId("metric-active-shifts")).toHaveTextContent("2");
      expect(screen.getByTestId("metric-completion-rate")).toHaveTextContent("66.7%");
    });
  });

  it("renders NotificationsCentrePage and supports marking notifications as read", async () => {
    vi.spyOn(apiClient, "get").mockResolvedValue({
      data: [
        {
          id: "notif-1",
          notification_type: "HANDOVER_SUBMITTED",
          type_display: "New Handover Submitted",
          title: "Handover Awaiting Acknowledgment: HND-DEMO-003",
          message: "Please review and acknowledge HND-DEMO-003.",
          is_read: false,
          created_at: new Date().toISOString(),
        },
      ],
    });
    const postSpy = vi.spyOn(apiClient, "post").mockResolvedValue({ data: {} });

    render(
      <MemoryRouter>
        <NotificationsCentrePage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(
        screen.getByText("Handover Awaiting Acknowledgment: HND-DEMO-003")
      ).toBeInTheDocument();
    });

    fireEvent.click(screen.getByTestId("mark-all-read-btn"));
    await waitFor(() => {
      expect(postSpy).toHaveBeenCalledWith("/notifications/mark-all-read/", {});
    });
  });

  it("renders TaskTrackingPage with carried-forward tasks and NLP override indicators", async () => {
    vi.spyOn(apiClient, "get").mockResolvedValueOnce({
      data: [
        {
          id: "t-1",
          description: "Inspect hydraulic return line B-nut seal on left main gear.",
          shift_name: "Morning Line Maint A",
          handover_code: "HND-DEMO-003",
          handover_report: "h-1",
          category: "Maintenance",
          priority: "Critical",
          status: "Pending",
          is_carried_forward: true,
          was_overridden: true,
          history: [],
        },
      ],
    });

    render(
      <MemoryRouter>
        <TaskTrackingPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(
        screen.getByText(
          "Inspect hydraulic return line B-nut seal on left main gear."
        )
      ).toBeInTheDocument();
      expect(
        screen.getByText("Carried Forward Across Shifts")
      ).toBeInTheDocument();
      expect(screen.getByText("NLP Overridden")).toBeInTheDocument();
    });
  });

  it("validates passwords matching and minimum length on SignUpPage", async () => {
    render(
      <MemoryRouter>
        <SignUpPage />
      </MemoryRouter>
    );

    // Click submit without entering data
    fireEvent.click(screen.getByTestId("signup-submit-button"));
    expect(screen.getByTestId("signup-error")).toHaveTextContent("Please enter your full name.");

    // Fill valid name, email, employee ID, but mismatched password
    fireEvent.change(screen.getByTestId("signup-fullname-input"), {
      target: { value: "Capt. Alice Waweru" },
    });
    fireEvent.change(screen.getByTestId("signup-email-input"), {
      target: { value: "awaweru@shiftsync.ac.ke" },
    });
    fireEvent.change(screen.getByTestId("signup-employee-id-input"), {
      target: { value: "KQ-9941" },
    });
    fireEvent.change(screen.getByTestId("signup-password-input"), {
      target: { value: "Short" },
    });
    fireEvent.change(screen.getByTestId("signup-confirm-password-input"), {
      target: { value: "Short" },
    });
    fireEvent.click(screen.getByTestId("signup-submit-button"));
    expect(screen.getByTestId("signup-error")).toHaveTextContent(
      "Password must be at least 8 characters long."
    );

    // Mismatched passwords
    fireEvent.change(screen.getByTestId("signup-password-input"), {
      target: { value: "SecurePass@2026!" },
    });
    fireEvent.change(screen.getByTestId("signup-confirm-password-input"), {
      target: { value: "DifferentPass@2026!" },
    });
    fireEvent.click(screen.getByTestId("signup-submit-button"));
    expect(screen.getByTestId("signup-error")).toHaveTextContent(
      "Password confirmation does not match."
    );
  });

  it("submits valid SignUpPage registration and sends data to /auth/register/", async () => {
    const postSpy = vi.spyOn(apiClient, "post").mockResolvedValueOnce({
      data: {
        detail: "Account created successfully.",
        user: { id: "u-new", email: "pilot@shiftsync.ac.ke" },
      },
    });

    render(
      <MemoryRouter>
        <SignUpPage />
      </MemoryRouter>
    );

    fireEvent.change(screen.getByTestId("signup-fullname-input"), {
      target: { value: "Capt. Alice Waweru" },
    });
    fireEvent.change(screen.getByTestId("signup-email-input"), {
      target: { value: "awaweru@shiftsync.ac.ke" },
    });
    fireEvent.change(screen.getByTestId("signup-employee-id-input"), {
      target: { value: "KQ-9941" },
    });
    fireEvent.change(screen.getByTestId("signup-password-input"), {
      target: { value: "SecurePass@2026!" },
    });
    fireEvent.change(screen.getByTestId("signup-confirm-password-input"), {
      target: { value: "SecurePass@2026!" },
    });

    fireEvent.click(screen.getByTestId("signup-submit-button"));

    await waitFor(() => {
      expect(postSpy).toHaveBeenCalledWith(
        "/auth/register/",
        expect.objectContaining({
          full_name: "Capt. Alice Waweru",
          email: "awaweru@shiftsync.ac.ke",
          employee_id: "KQ-9941",
          personnel_category: "ENGINEER",
          password: "SecurePass@2026!",
          confirm_password: "SecurePass@2026!",
          privacy_terms_accepted: true,
        })
      );
    });
  });
});
