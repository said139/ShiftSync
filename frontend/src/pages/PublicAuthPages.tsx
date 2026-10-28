import React, { useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import {
  AlertCircle,
  CheckCircle2,
  KeyRound,
  Lock,
  ShieldAlert,
  Sparkles,
} from "lucide-react";
import { useAuth } from "../context/AuthContext";
import { apiClient } from "../api/client";

export const LoginPage: React.FC = () => {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
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
      setError(
        err.response?.data?.detail ||
          "Authentication failed. Please check your credentials and try again."
      );
    } finally {
      setSubmitting(false);
    }
  };

  const fillDemo = (demoEmail: string) => {
    setEmail(demoEmail);
    setPassword("ShiftSync@2026!");
    setError(null);
  };

  return (
    <div
      style={{
        minHeight: "100vh",
        background: "linear-gradient(135deg, var(--navy-950) 0%, var(--navy-900) 60%, var(--navy-800) 100%)",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        padding: "1.5rem",
      }}
    >
      <div className="card" style={{ maxWidth: "460px", width: "100%", padding: "2rem" }}>
        <div style={{ display: "flex", alignItems: "center", gap: "0.75rem", marginBottom: "1.25rem" }}>
          <div className="brand-icon" style={{ width: 42, height: 42, fontSize: "1.1rem" }}>
            SS
          </div>
          <div>
            <h1 style={{ fontSize: "1.35rem", fontWeight: 700, color: "var(--navy-900)" }}>
              ShiftSync Portal
            </h1>
            <p style={{ fontSize: "0.8rem", color: "var(--slate-500)" }}>
              Formal Shift Handover Management & NLP Task Classification
            </p>
          </div>
        </div>

        {error && (
          <div className="alert alert-error" role="alert" data-testid="login-error">
            <AlertCircle size={18} style={{ flexShrink: 0, marginTop: 2 }} />
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} noValidate>
          <div className="form-group">
            <label htmlFor="login-email" className="form-label">
              Work Email Address
            </label>
            <input
              id="login-email"
              type="email"
              className="form-control"
              placeholder="name@shiftsync.ac.ke"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              autoComplete="email"
              data-testid="login-email-input"
            />
          </div>

          <div className="form-group">
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <label htmlFor="login-password" className="form-label">
                Password
              </label>
              <Link
                to="/forgot-password"
                style={{ fontSize: "0.78rem", color: "var(--teal-700)", fontWeight: 600 }}
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
            style={{ width: "100%", marginTop: "0.5rem", padding: "0.65rem" }}
            disabled={submitting}
            data-testid="login-submit-button"
          >
            <Lock size={16} />
            <span>{submitting ? "Authenticating..." : "Sign In to ShiftSync"}</span>
          </button>
        </form>

        <div
          style={{
            marginTop: "1.5rem",
            paddingTop: "1.1rem",
            borderTop: "1px solid var(--slate-200)",
          }}
        >
          <div
            style={{
              fontSize: "0.73rem",
              fontWeight: 700,
              textTransform: "uppercase",
              color: "var(--slate-500)",
              marginBottom: "0.55rem",
              display: "flex",
              alignItems: "center",
              gap: "0.35rem",
            }}
          >
            <Sparkles size={13} />
            <span>Seeded Demonstration Accounts (Dev Environment)</span>
          </div>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0.45rem" }}>
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
          <p style={{ fontSize: "0.73rem", color: "var(--slate-500)", marginTop: "0.6rem" }}>
            Account creation follows administrative provisioning. Contact your System Administrator for new credentials.
          </p>
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
      <div className="card" style={{ maxWidth: "460px", width: "100%", padding: "2rem" }}>
        <div style={{ display: "flex", alignItems: "center", gap: "0.65rem", marginBottom: "1rem" }}>
          <KeyRound size={24} color="var(--teal-600)" />
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
              Enter your registered work email to generate a time-limited password reset token.
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
      <div style={{ display: "flex", alignItems: "center", gap: "0.75rem", color: "var(--red-700)", marginBottom: "1rem" }}>
        <ShieldAlert size={32} />
        <h1 style={{ fontSize: "1.4rem", fontWeight: 700 }}>403 — Access Denied</h1>
      </div>
      <p style={{ color: "var(--slate-600)", marginBottom: "1rem" }}>
        Your current role (<strong>{user?.role_display || "Unauthenticated"}</strong>) is not authorised to access this operational resource. All role permissions are enforced by ShiftSync security policies.
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
