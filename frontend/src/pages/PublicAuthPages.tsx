import React, { useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import {
  AlertCircle,
  ArrowRight,
  Briefcase,
  CheckCircle2,
  KeyRound,
  Lock,
  Mail,
  Phone,
  Plane,
  Shield,
  ShieldAlert,
  Sparkles,
  User,
  UserCheck,
  UserPlus,
} from "lucide-react";
import { useAuth } from "../context/AuthContext";
import { apiClient } from "../api/client";

export const LoginPage: React.FC = () => {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();

  const initialEmail = searchParams.get("email") || "";
  const justRegistered = searchParams.get("registered") === "true" || searchParams.get("registered") === "1";

  const [email, setEmail] = useState(initialEmail);
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(
    justRegistered ? "Account created successfully! Please sign in with your credentials." : null
  );
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSuccessMsg(null);
    if (!email.trim() || !password) {
      setError("Please enter both your email address and password.");
      return;
    }
    setSubmitting(true);
    try {
      const loggedInUser = await login(email.trim(), password);
      if (loggedInUser.role === "SUPERVISOR") {
        navigate("/supervisor/dashboard");
      } else {
        navigate("/dashboard");
      }
    } catch (err: any) {
      const detail =
        err.response?.data?.detail ||
        "Authentication failed. Please check your credentials and try again.";
      setError(detail);
    } finally {
      setSubmitting(false);
    }
  };

  const fillDemo = (demoEmail: string) => {
    setEmail(demoEmail);
    setPassword("ShiftSync@2026!");
    setError(null);
    setSuccessMsg(null);
  };

  return (
    <div
      style={{
        minHeight: "100vh",
        background: "linear-gradient(135deg, #0a0d13 0%, #141820 50%, #202735 100%)",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        padding: "1.5rem",
      }}
    >
      <div className="card" style={{ maxWidth: "480px", width: "100%", padding: "2.25rem", position: "relative", overflow: "hidden" }}>
        {/* Kenya Airways Top Ribbon Accent */}
        <div style={{ position: "absolute", top: 0, left: 0, right: 0, display: "flex", height: "4px" }}>
          <div style={{ flex: 5, backgroundColor: "var(--kq-red-600)" }} />
          <div style={{ flex: 2, backgroundColor: "var(--kq-gold-500)" }} />
          <div style={{ flex: 2, backgroundColor: "var(--green-600)" }} />
        </div>

        {/* Brand Header */}
        <div style={{ display: "flex", alignItems: "center", gap: "0.85rem", marginBottom: "1.5rem" }}>
          <div
            className="brand-icon"
            style={{
              width: 46,
              height: 46,
              fontSize: "1.15rem",
              background: "linear-gradient(135deg, var(--kq-red-600) 0%, var(--kq-red-800) 100%)",
              border: "1px solid var(--kq-gold-500)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
            }}
          >
            <Plane size={24} color="#fff" />
          </div>
          <div>
            <div style={{ display: "flex", alignItems: "center", gap: "0.4rem" }}>
              <span className="kq-tag">KENYA AIRWAYS</span>
              <span style={{ fontSize: "0.72rem", color: "var(--slate-500)", fontWeight: 600 }}>JKIA HUB</span>
            </div>
            <h1 style={{ fontSize: "1.35rem", fontWeight: 700, color: "var(--navy-900)", lineHeight: 1.25 }}>
              ShiftSync Portal
            </h1>
            <p style={{ fontSize: "0.8rem", color: "var(--slate-500)" }}>
              Flight Operations & Line Maintenance Shift Handover
            </p>
          </div>
        </div>

        {successMsg && (
          <div className="alert alert-success" role="status">
            <CheckCircle2 size={18} style={{ flexShrink: 0, marginTop: 2 }} />
            <span>{successMsg}</span>
          </div>
        )}

        {error && (
          <div className="alert alert-error" role="alert" data-testid="login-error">
            <AlertCircle size={18} style={{ flexShrink: 0, marginTop: 2 }} />
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} noValidate>
          <div className="form-group">
            <label htmlFor="login-email" className="form-label">
              Work Email Address or Staff ID
            </label>
            <div style={{ position: "relative" }}>
              <input
                id="login-email"
                type="text"
                className="form-control"
                placeholder="name@shiftsync.ac.ke or KQ-XXXX"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                autoComplete="username"
                data-testid="login-email-input"
              />
            </div>
          </div>

          <div className="form-group">
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <label htmlFor="login-password" className="form-label">
                Password
              </label>
              <Link
                to="/forgot-password"
                style={{ fontSize: "0.78rem", color: "var(--kq-red-600)", fontWeight: 600 }}
              >
                Forgot password?
              </Link>
            </div>
            <input
              id="login-password"
              type="password"
              className="form-control"
              placeholder="••••••••••••"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              autoComplete="current-password"
              data-testid="login-password-input"
            />
          </div>

          <button
            type="submit"
            className="btn btn-primary"
            style={{ width: "100%", marginTop: "0.5rem", padding: "0.7rem", fontSize: "0.95rem" }}
            disabled={submitting}
            data-testid="login-submit-button"
          >
            <Lock size={16} />
            <span>{submitting ? "Verifying Credentials..." : "Sign In to ShiftSync"}</span>
          </button>
        </form>

        {/* Prominent Sign Up CTA Link */}
        <div
          style={{
            marginTop: "1.25rem",
            padding: "0.9rem 1rem",
            background: "var(--kq-red-50)",
            border: "1px solid var(--kq-red-100)",
            borderRadius: "8px",
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
          }}
        >
          <div>
            <div style={{ fontSize: "0.85rem", fontWeight: 700, color: "var(--kq-red-900)" }}>
              New crew member?
            </div>
            <div style={{ fontSize: "0.75rem", color: "var(--slate-600)" }}>
              Create an operational pilot, engineer, or crew account.
            </div>
          </div>
          <Link
            to="/signup"
            className="btn btn-sm"
            style={{
              backgroundColor: "var(--kq-red-600)",
              color: "#fff",
              fontWeight: 700,
              fontSize: "0.8rem",
              whiteSpace: "nowrap",
            }}
            data-testid="go-to-signup-btn"
          >
            <UserPlus size={14} />
            <span>Sign Up</span>
          </Link>
        </div>

        {/* Kenya Airways Crew Demonstration Accounts */}
        <div
          style={{
            marginTop: "1.25rem",
            paddingTop: "1.1rem",
            borderTop: "1px solid var(--slate-200)",
          }}
        >
          <div
            style={{
              fontSize: "0.73rem",
              fontWeight: 700,
              textTransform: "uppercase",
              color: "var(--kq-red-700)",
              marginBottom: "0.55rem",
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
            }}
          >
            <span style={{ display: "flex", alignItems: "center", gap: "0.35rem" }}>
              <Plane size={13} color="var(--kq-red-600)" />
              <span>Kenya Airways Flight & Line Crew (Click to Sign In)</span>
            </span>
            <span style={{ fontSize: "0.68rem", color: "var(--slate-400)" }}>Dev / Demo</span>
          </div>

          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0.45rem", marginBottom: "0.6rem" }}>
            <button
              type="button"
              className="btn btn-secondary btn-sm"
              style={{ textAlign: "left", padding: "0.45rem 0.6rem", display: "flex", flexDirection: "column", gap: "0.15rem" }}
              onClick={() => fillDemo("said@kq.ac.ke")}
              data-testid="demo-kq-said-btn"
            >
              <strong style={{ fontSize: "0.78rem", color: "var(--navy-900)" }}>Eng. Said Marika</strong>
              <span style={{ fontSize: "0.7rem", color: "var(--slate-500)" }}>said@kq.ac.ke • Admin</span>
            </button>
            <button
              type="button"
              className="btn btn-secondary btn-sm"
              style={{ textAlign: "left", padding: "0.45rem 0.6rem", display: "flex", flexDirection: "column", gap: "0.15rem" }}
              onClick={() => fillDemo("david@kq.ac.ke")}
              data-testid="demo-kq-david-btn"
            >
              <strong style={{ fontSize: "0.78rem", color: "var(--navy-900)" }}>Eng. David Ochieng</strong>
              <span style={{ fontSize: "0.7rem", color: "var(--slate-500)" }}>david@kq.ac.ke • Line Maint</span>
            </button>
            <button
              type="button"
              className="btn btn-secondary btn-sm"
              style={{ textAlign: "left", padding: "0.45rem 0.6rem", display: "flex", flexDirection: "column", gap: "0.15rem" }}
              onClick={() => fillDemo("amina@kq.ac.ke")}
              data-testid="demo-kq-amina-btn"
            >
              <strong style={{ fontSize: "0.78rem", color: "var(--navy-900)" }}>Eng. Amina Hassan</strong>
              <span style={{ fontSize: "0.7rem", color: "var(--slate-500)" }}>amina@kq.ac.ke • Line Maint</span>
            </button>
            <button
              type="button"
              className="btn btn-secondary btn-sm"
              style={{ textAlign: "left", padding: "0.45rem 0.6rem", display: "flex", flexDirection: "column", gap: "0.15rem" }}
              onClick={() => fillDemo("grace@kq.ac.ke")}
              data-testid="demo-kq-grace-btn"
            >
              <strong style={{ fontSize: "0.78rem", color: "var(--navy-900)" }}>Capt. Grace Wanjiku</strong>
              <span style={{ fontSize: "0.7rem", color: "var(--slate-500)" }}>grace@kq.ac.ke • QA Sup</span>
            </button>
          </div>

          {/* Quick-fill by Role (Legacy & Automated Test Compatibility) */}
          <div style={{ marginTop: "0.75rem", paddingTop: "0.6rem", borderTop: "1px dashed var(--slate-200)" }}>
            <div style={{ fontSize: "0.7rem", fontWeight: 700, textTransform: "uppercase", color: "var(--slate-500)", marginBottom: "0.4rem" }}>
              Quick-Fill By Operational Role
            </div>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0.35rem" }}>
              <button
                type="button"
                className="btn btn-secondary btn-sm"
                onClick={() => fillDemo("outgoing@shiftsync.ac.ke")}
                data-testid="demo-outgoing-btn"
              >
                Outgoing Worker
              </button>
              <button
                type="button"
                onClick={() => fillDemo("incoming@shiftsync.ac.ke")}
                className="btn btn-secondary btn-sm"
                data-testid="demo-incoming-btn"
              >
                Incoming Worker
              </button>
              <button
                type="button"
                onClick={() => fillDemo("supervisor@shiftsync.ac.ke")}
                className="btn btn-secondary btn-sm"
                data-testid="demo-supervisor-btn"
              >
                Supervisor
              </button>
              <button
                type="button"
                onClick={() => fillDemo("admin@shiftsync.ac.ke")}
                className="btn btn-secondary btn-sm"
                data-testid="demo-admin-btn"
              >
                System Admin
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export const SignUpPage: React.FC = () => {
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    full_name: "",
    email: "",
    employee_id: "",
    personnel_category: "ENGINEER",
    department: "Line Maintenance & Hangar Engineering",
    phone_number: "",
    password: "",
    confirm_password: "",
    privacy_terms_accepted: true,
  });

  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const categoryDepartments: Record<string, string> = {
    PILOT: "Flight Operations (B787 / B737 Fleet)",
    ENGINEER: "Line Maintenance & Hangar Engineering",
    CABIN_CREW: "Cabin Services & In-Flight Operations",
  };

  const handleCategoryChange = (cat: string) => {
    setFormData((prev) => ({
      ...prev,
      personnel_category: cat,
      department: categoryDepartments[cat] || prev.department,
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    // Client-side validation
    if (!formData.full_name.trim()) {
      setError("Please enter your full name.");
      return;
    }
    if (!formData.email.trim() || !formData.email.includes("@")) {
      setError("Please enter a valid work email address.");
      return;
    }
    if (!formData.employee_id.trim() || formData.employee_id.trim().length < 3) {
      setError("Staff ID must be at least 3 characters (e.g., KQ-8492).");
      return;
    }
    if (formData.password.length < 8) {
      setError("Password must be at least 8 characters long.");
      return;
    }
    if (formData.password !== formData.confirm_password) {
      setError("Password confirmation does not match.");
      return;
    }
    if (!formData.privacy_terms_accepted) {
      setError("You must accept the Kenya Airways ShiftSync operational safety protocols.");
      return;
    }

    setSubmitting(true);
    try {
      const payload = {
        full_name: formData.full_name.trim(),
        email: formData.email.trim().toLowerCase(),
        employee_id: formData.employee_id.trim().toUpperCase(),
        personnel_category: formData.personnel_category,
        department: formData.department.trim(),
        phone_number: formData.phone_number.trim(),
        password: formData.password,
        confirm_password: formData.confirm_password,
        privacy_terms_accepted: formData.privacy_terms_accepted,
      };

      await apiClient.post("/auth/register/", payload);

      // Navigate to login with success flag and prefilled email
      navigate(`/login?registered=1&email=${encodeURIComponent(payload.email)}`);
    } catch (err: any) {
      const data = err.response?.data;
      if (typeof data === "string") {
        setError(data);
      } else if (data?.detail) {
        setError(data.detail);
      } else if (data && typeof data === "object") {
        // Collect field validation errors
        const messages = Object.entries(data)
          .map(([field, errs]) => {
            const msg = Array.isArray(errs) ? errs.join(" ") : String(errs);
            const fieldName = field.replace(/_/g, " ");
            return `${fieldName}: ${msg}`;
          })
          .join(" | ");
        setError(messages || "Registration failed. Please verify your details.");
      } else {
        setError("Network or server error during registration. Please try again.");
      }
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div
      style={{
        minHeight: "100vh",
        background: "linear-gradient(135deg, #0a0d13 0%, #141820 50%, #202735 100%)",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        padding: "1.5rem",
      }}
    >
      <div className="card" style={{ maxWidth: "560px", width: "100%", padding: "2.25rem", position: "relative", overflow: "hidden" }}>
        {/* Kenya Airways Top Ribbon Accent */}
        <div style={{ position: "absolute", top: 0, left: 0, right: 0, display: "flex", height: "4px" }}>
          <div style={{ flex: 5, backgroundColor: "var(--kq-red-600)" }} />
          <div style={{ flex: 2, backgroundColor: "var(--kq-gold-500)" }} />
          <div style={{ flex: 2, backgroundColor: "var(--green-600)" }} />
        </div>

        {/* Brand Header */}
        <div style={{ display: "flex", alignItems: "center", gap: "0.85rem", marginBottom: "1.25rem" }}>
          <div
            className="brand-icon"
            style={{
              width: 44,
              height: 44,
              fontSize: "1.1rem",
              background: "linear-gradient(135deg, var(--kq-red-600) 0%, var(--kq-red-800) 100%)",
              border: "1px solid var(--kq-gold-500)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
            }}
          >
            <UserPlus size={22} color="#fff" />
          </div>
          <div>
            <div style={{ display: "flex", alignItems: "center", gap: "0.4rem" }}>
              <span className="kq-tag">KENYA AIRWAYS</span>
              <span style={{ fontSize: "0.72rem", color: "var(--slate-500)", fontWeight: 600 }}>CREW ENROLMENT</span>
            </div>
            <h1 style={{ fontSize: "1.35rem", fontWeight: 700, color: "var(--navy-900)", lineHeight: 1.25 }}>
              Sign Up for ShiftSync
            </h1>
            <p style={{ fontSize: "0.8rem", color: "var(--slate-500)" }}>
              Create an operational flight crew or maintenance account
            </p>
          </div>
        </div>

        {error && (
          <div className="alert alert-error" role="alert" data-testid="signup-error">
            <AlertCircle size={18} style={{ flexShrink: 0, marginTop: 2 }} />
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} noValidate>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0.85rem" }}>
            <div className="form-group" style={{ gridColumn: "1 / -1" }}>
              <label htmlFor="signup-fullname" className="form-label">
                Full Name <span className="required">*</span>
              </label>
              <input
                id="signup-fullname"
                type="text"
                className="form-control"
                placeholder="Capt. / Eng. Jane Doe"
                value={formData.full_name}
                onChange={(e) => setFormData({ ...formData, full_name: e.target.value })}
                required
                data-testid="signup-fullname-input"
              />
            </div>

            <div className="form-group">
              <label htmlFor="signup-email" className="form-label">
                Work Email <span className="required">*</span>
              </label>
              <input
                id="signup-email"
                type="email"
                className="form-control"
                placeholder="name@shiftsync.ac.ke"
                value={formData.email}
                onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                required
                data-testid="signup-email-input"
              />
            </div>

            <div className="form-group">
              <label htmlFor="signup-employee-id" className="form-label">
                Staff / Employee ID <span className="required">*</span>
              </label>
              <input
                id="signup-employee-id"
                type="text"
                className="form-control"
                placeholder="KQ-7842"
                value={formData.employee_id}
                onChange={(e) => setFormData({ ...formData, employee_id: e.target.value.toUpperCase() })}
                required
                data-testid="signup-employee-id-input"
              />
            </div>
          </div>

          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0.85rem" }}>
            <div className="form-group">
              <label htmlFor="signup-category" className="form-label">
                Personnel Category <span className="required">*</span>
              </label>
              <select
                id="signup-category"
                className="form-control"
                value={formData.personnel_category}
                onChange={(e) => handleCategoryChange(e.target.value)}
                data-testid="signup-category-select"
              >
                <option value="ENGINEER">Aeronautical Engineer / Line Maintenance</option>
                <option value="PILOT">Pilot / Flight Operations Crew</option>
                <option value="CABIN_CREW">Cabin Crew / In-Flight Services</option>
              </select>
            </div>

            <div className="form-group">
              <label htmlFor="signup-phone" className="form-label">
                Phone Number (Optional)
              </label>
              <input
                id="signup-phone"
                type="tel"
                className="form-control"
                placeholder="+254 7XX XXX XXX"
                value={formData.phone_number}
                onChange={(e) => setFormData({ ...formData, phone_number: e.target.value })}
                data-testid="signup-phone-input"
              />
            </div>
          </div>

          <div className="form-group">
            <label htmlFor="signup-department" className="form-label">
              Operational Department
            </label>
            <input
              id="signup-department"
              type="text"
              className="form-control"
              value={formData.department}
              onChange={(e) => setFormData({ ...formData, department: e.target.value })}
              data-testid="signup-department-input"
            />
          </div>

          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0.85rem" }}>
            <div className="form-group">
              <label htmlFor="signup-password" className="form-label">
                Password <span className="required">*</span>
              </label>
              <input
                id="signup-password"
                type="password"
                className="form-control"
                placeholder="Min 8 characters"
                value={formData.password}
                onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                required
                minLength={8}
                data-testid="signup-password-input"
              />
            </div>

            <div className="form-group">
              <label htmlFor="signup-confirm-password" className="form-label">
                Confirm Password <span className="required">*</span>
              </label>
              <input
                id="signup-confirm-password"
                type="password"
                className="form-control"
                placeholder="Repeat password"
                value={formData.confirm_password}
                onChange={(e) => setFormData({ ...formData, confirm_password: e.target.value })}
                required
                data-testid="signup-confirm-password-input"
              />
            </div>
          </div>

          <div className="form-group" style={{ marginTop: "0.25rem" }}>
            <label style={{ display: "flex", alignItems: "flex-start", gap: "0.55rem", cursor: "pointer", fontSize: "0.82rem", color: "var(--navy-900)" }}>
              <input
                type="checkbox"
                checked={formData.privacy_terms_accepted}
                onChange={(e) => setFormData({ ...formData, privacy_terms_accepted: e.target.checked })}
                style={{ marginTop: "0.2rem", accentColor: "var(--kq-red-600)" }}
                data-testid="signup-terms-checkbox"
              />
              <span>
                I agree to the Kenya Airways Shift Handover safety protocol, audit logging, and data privacy policies.
              </span>
            </label>
          </div>

          <button
            type="submit"
            className="btn btn-primary"
            style={{ width: "100%", padding: "0.7rem", fontSize: "0.95rem", marginTop: "0.5rem" }}
            disabled={submitting}
            data-testid="signup-submit-button"
          >
            <UserCheck size={16} />
            <span>{submitting ? "Registering Crew Account..." : "Create Account & Continue to Sign In"}</span>
          </button>
        </form>

        <div style={{ marginTop: "1.25rem", textAlign: "center", fontSize: "0.85rem", color: "var(--slate-600)" }}>
          Already have an operational account?{" "}
          <Link to="/login" style={{ color: "var(--kq-red-600)", fontWeight: 700 }} data-testid="signup-login-link">
            Sign In here
          </Link>
        </div>
      </div>
    </div>
  );
};

export const PasswordRecoveryPage: React.FC = () => {
  const [searchParams] = useSearchParams();
  const initialToken = searchParams.get("token") || "";
  const [email, setEmail] = useState("");
  const [resetToken, setResetToken] = useState(initialToken);
  const [newPassword, setNewPassword] = useState("");
  const [step, setStep] = useState<"request" | "confirm">(
    initialToken ? "confirm" : "request"
  );
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleRequestToken = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setMessage(null);
    setLoading(true);
    try {
      const res = await apiClient.post("/auth/password-recovery/", { email });
      setMessage(res.data.detail);
      if (res.data.reset_token) {
        setResetToken(res.data.reset_token);
      }
      setStep("confirm");
    } catch (err: any) {
      setError(
        err.response?.data?.detail || "Unable to process password recovery request."
      );
    } finally {
      setLoading(false);
    }
  };

  const handleConfirmReset = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setMessage(null);
    setLoading(true);
    try {
      const res = await apiClient.post("/auth/password-reset/", {
        token: resetToken,
        new_password: newPassword,
      });
      setMessage(res.data.detail);
    } catch (err: any) {
      const data = err.response?.data;
      setError(
        data?.detail ||
          (Array.isArray(data?.new_password) ? data.new_password.join(" ") : null) ||
          "Password reset failed. Check your token and password complexity."
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div
      style={{
        minHeight: "100vh",
        background: "var(--navy-900)",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        padding: "1.5rem",
      }}
    >
      <div className="card" style={{ maxWidth: "460px", width: "100%", padding: "2rem", position: "relative", overflow: "hidden" }}>
        <div style={{ position: "absolute", top: 0, left: 0, right: 0, display: "flex", height: "4px" }}>
          <div style={{ flex: 5, backgroundColor: "var(--kq-red-600)" }} />
          <div style={{ flex: 2, backgroundColor: "var(--kq-gold-500)" }} />
          <div style={{ flex: 2, backgroundColor: "var(--green-600)" }} />
        </div>

        <div style={{ display: "flex", alignItems: "center", gap: "0.65rem", marginBottom: "1rem" }}>
          <KeyRound size={24} color="var(--kq-red-600)" />
          <h1 style={{ fontSize: "1.25rem", fontWeight: 700 }}>
            Password Recovery & Reset
          </h1>
        </div>

        {message && (
          <div className="alert alert-success">
            <CheckCircle2 size={18} style={{ flexShrink: 0 }} />
            <span>{message}</span>
          </div>
        )}
        {error && (
          <div className="alert alert-error">
            <AlertCircle size={18} style={{ flexShrink: 0 }} />
            <span>{error}</span>
          </div>
        )}

        {step === "request" ? (
          <form onSubmit={handleRequestToken}>
            <p style={{ fontSize: "0.85rem", color: "var(--slate-600)", marginBottom: "1rem" }}>
              Enter your registered Kenya Airways work email to generate a time-limited password reset token.
            </p>
            <div className="form-group">
              <label htmlFor="rec-email" className="form-label">
                Work Email Address
              </label>
              <input
                id="rec-email"
                type="email"
                className="form-control"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
              />
            </div>
            <button type="submit" className="btn btn-primary" style={{ width: "100%" }} disabled={loading}>
              {loading ? "Generating..." : "Request Password Reset Token"}
            </button>
          </form>
        ) : (
          <form onSubmit={handleConfirmReset}>
            <div className="form-group">
              <label htmlFor="reset-token" className="form-label">
                Recovery Token
              </label>
              <input
                id="reset-token"
                type="text"
                className="form-control mono"
                value={resetToken}
                onChange={(e) => setResetToken(e.target.value)}
                required
              />
            </div>
            <div className="form-group">
              <label htmlFor="reset-new-pw" className="form-label">
                New Password (minimum 8 characters)
              </label>
              <input
                id="reset-new-pw"
                type="password"
                className="form-control"
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                required
                minLength={8}
              />
            </div>
            <button type="submit" className="btn btn-primary" style={{ width: "100%" }} disabled={loading}>
              {loading ? "Updating Password..." : "Confirm New Password"}
            </button>
          </form>
        )}

        <div style={{ marginTop: "1.25rem", display: "flex", justifyContent: "space-between", fontSize: "0.85rem" }}>
          <button
            type="button"
            className="btn btn-secondary btn-sm"
            onClick={() => setStep(step === "request" ? "confirm" : "request")}
          >
            {step === "request" ? "I already have a token" : "Request another token"}
          </button>
          <Link to="/login" className="btn btn-secondary btn-sm">
            Back to Sign In
          </Link>
        </div>
      </div>
    </div>
  );
};

export const AccessDeniedPage: React.FC = () => {
  const { user } = useAuth();
  return (
    <div style={{ maxWidth: "560px", margin: "4rem auto" }} className="card">
      <div style={{ display: "flex", alignItems: "center", gap: "0.75rem", color: "var(--red-600)", marginBottom: "1rem" }}>
        <ShieldAlert size={32} />
        <h1 style={{ fontSize: "1.4rem", fontWeight: 700 }}>403 — Access Denied</h1>
      </div>
      <p style={{ color: "var(--slate-600)", marginBottom: "1rem" }}>
        Your current role (<strong>{user?.role_display || "Unauthenticated"}</strong>) is not authorised to access this operational resource. All role permissions are strictly enforced by Kenya Airways ShiftSync policies.
      </p>
      <Link to="/dashboard" className="btn btn-primary">
        Return to Authorised Dashboard
      </Link>
    </div>
  );
};

export const NotFoundPage: React.FC = () => {
  return (
    <div style={{ maxWidth: "560px", margin: "4rem auto" }} className="card">
      <h1 style={{ fontSize: "1.5rem", fontWeight: 700, marginBottom: "0.5rem" }}>
        404 — Page Not Found
      </h1>
      <p style={{ color: "var(--slate-600)", marginBottom: "1.25rem" }}>
        The ShiftSync route you requested does not exist or has been moved.
      </p>
      <Link to="/dashboard" className="btn btn-primary">
        Go to Dashboard Overview
      </Link>
    </div>
  );
};
