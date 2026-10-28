import React, { createContext, useContext, useEffect, useRef, useState } from "react";
import { getAccessToken } from "../api/client";
import { useAuth } from "./AuthContext";

export interface LiveToast {
  id: string;
  title: string;
  message: string;
  type: "info" | "success" | "warning" | "alert";
  timestamp: string;
}

interface WebSocketContextValue {
  connected: boolean;
  lastEvent: any | null;
  activeToast: LiveToast | null;
  dismissToast: () => void;
  sendPing: () => void;
}

const WebSocketContext = createContext<WebSocketContextValue>({
  connected: false,
  lastEvent: null,
  activeToast: null,
  dismissToast: () => {},
  sendPing: () => {},
});

export const useWebSocket = () => useContext(WebSocketContext);

export const WebSocketProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { user } = useAuth();
  const [connected, setConnected] = useState<boolean>(false);
  const [lastEvent, setLastEvent] = useState<any | null>(null);
  const [activeToast, setActiveToast] = useState<LiveToast | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<any>(null);

  const dismissToast = () => setActiveToast(null);

  const triggerToast = (title: string, message: string, type: "info" | "success" | "warning" | "alert" = "info") => {
    const toast: LiveToast = {
      id: Date.now().toString(),
      title,
      message,
      type,
      timestamp: new Date().toLocaleTimeString(),
    };
    setActiveToast(toast);

    // Auto dismiss toast after 6 seconds
    setTimeout(() => {
      setActiveToast((curr) => (curr?.id === toast.id ? null : curr));
    }, 6000);
  };

  const connect = () => {
    if (!user) return;
    const token = getAccessToken();
    if (!token) return;

    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) return;

    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    // Connect to Django ASGI Daphne backend on port 8000
    const host = window.location.hostname === "localhost" ? "127.0.0.1:8000" : `${window.location.hostname}:8000`;
    const wsUrl = `${protocol}//${host}/ws/live/?token=${encodeURIComponent(token)}`;

    try {
      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.onopen = () => {
        setConnected(true);
      };

      ws.onmessage = (event) => {
        try {
          const payload = JSON.parse(event.data);
          setLastEvent(payload);

          // Handle live server push events
          if (payload.type === "SYSTEM_CONNECTED") {
            // Handshake confirmed
          } else if (payload.event === "NEW_NOTIFICATION") {
            triggerToast(
              payload.data.title || "New ShiftSync Notification",
              payload.data.message || "A new notification requires your attention.",
              "info"
            );
          } else if (payload.event === "HANDOVER_SUBMITTED") {
            triggerToast(
              `Handover Submitted: ${payload.data.report_code}`,
              `${payload.data.submitting_worker} submitted handover for '${payload.data.shift_name}' (${payload.data.task_count} tasks).`,
              payload.data.has_safety_incident ? "alert" : "warning"
            );
          } else if (payload.event === "HANDOVER_ACKNOWLEDGED") {
            triggerToast(
              `Handover Acknowledged: ${payload.data.report_code}`,
              `Custody confirmed by ${payload.data.acknowledged_by}.`,
              "success"
            );
          } else if (payload.event === "DASHBOARD_METRIC_UPDATE") {
            // Background telemetry update
          }
        } catch {
          // Ignore parse errors on raw messages
        }
      };

      ws.onerror = () => {
        setConnected(false);
      };

      ws.onclose = () => {
        setConnected(false);
        // Attempt reconnect in 4 seconds if user is still logged in
        reconnectTimeoutRef.current = setTimeout(() => {
          if (user) {
            connect();
          }
        }, 4000);
      };
    } catch {
      setConnected(false);
    }
  };

  useEffect(() => {
    if (user) {
      connect();
    } else {
      if (wsRef.current) {
        wsRef.current.close();
        wsRef.current = null;
      }
      setConnected(false);
    }

    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [user]);

  const sendPing = () => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: "PING" }));
    }
  };

  return (
    <WebSocketContext.Provider
      value={{
        connected,
        lastEvent,
        activeToast,
        dismissToast,
        sendPing,
      }}
    >
      {children}

      {/* Floating Live Telemetry Toast */}
      {activeToast && (
        <aside
          role="region"
          aria-label="Live System Alerts"
          className="live-ws-toast"
          style={{
            position: "fixed",
            bottom: "1.5rem",
            right: "1.5rem",
            zIndex: 9999,
            maxWidth: "380px",
            background: "#0f172a",
            color: "#fff",
            borderRadius: "8px",
            boxShadow: "0 10px 25px -5px rgba(0,0,0,0.3), 0 8px 10px -6px rgba(0,0,0,0.3)",
            border: activeToast.type === "alert"
              ? "2px solid #c8102e"
              : activeToast.type === "success"
              ? "2px solid #007a3d"
              : activeToast.type === "warning"
              ? "2px solid #e5a823"
              : "2px solid #38bdf8",
            overflow: "hidden",
            animation: "slideInUp 0.3s cubic-bezier(0.16, 1, 0.3, 1)",
          }}
          data-testid="live-ws-toast"
        >
          {/* Kenya Airways Top Color Stripe */}
          <div style={{ display: "flex", height: "3px" }}>
            <div style={{ flex: 5, backgroundColor: "#c8102e" }} />
            <div style={{ flex: 2, backgroundColor: "#e5a823" }} />
            <div style={{ flex: 2, backgroundColor: "#007a3d" }} />
          </div>

          <div style={{ padding: "0.85rem 1.1rem" }}>
            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "0.3rem" }}>
              <div style={{ display: "flex", alignItems: "center", gap: "0.4rem" }}>
                <span
                  style={{
                    width: 7,
                    height: 7,
                    borderRadius: "50%",
                    backgroundColor: activeToast.type === "alert" ? "#ef4444" : activeToast.type === "success" ? "#22c55e" : "#e5a823",
                    display: "inline-block",
                  }}
                />
                <span style={{ fontSize: "0.7rem", fontWeight: 800, textTransform: "uppercase", letterSpacing: "0.05em", color: "#94a3b8" }}>
                  Live WebSocket Push &bull; {activeToast.timestamp}
                </span>
              </div>
              <button
                type="button"
                onClick={dismissToast}
                style={{
                  background: "transparent",
                  border: "none",
                  color: "#94a3b8",
                  cursor: "pointer",
                  fontSize: "1rem",
                  lineHeight: 1,
                  padding: "0.2rem",
                }}
                aria-label="Close alert"
              >
                &times;
              </button>
            </div>

            <div style={{ fontWeight: 700, fontSize: "0.88rem", color: "#fff", marginBottom: "0.25rem" }}>
              {activeToast.title}
            </div>
            <div style={{ fontSize: "0.78rem", color: "#cbd5e1", lineHeight: 1.45 }}>
              {activeToast.message}
            </div>
          </div>
        </aside>
      )}
    </WebSocketContext.Provider>
  );
};
