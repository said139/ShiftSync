import React from "react";
import {
  AlertTriangle,
  CheckCircle2,
  Clock,
  FileEdit,
  Flame,
  Info,
  Send,
  ShieldAlert,
  Wrench,
} from "lucide-react";

/**
 * Accessible status & priority badges using colour + icon + text
 * so status is never communicated through colour alone (Section 11).
 */
export const HandoverStatusBadge: React.FC<{ status: string }> = ({
  status,
}) => {
  const normalized = (status || "").toUpperCase();
  if (normalized === "ACKNOWLEDGED") {
    return (
      <span className="badge badge-green" title="Handover formally acknowledged">
        <CheckCircle2 size={13} aria-hidden="true" />
        <span>Acknowledged</span>
      </span>
    );
  }
  if (normalized === "SUBMITTED") {
    return (
      <span
        className="badge badge-amber"
        title="Handover submitted and awaiting incoming acknowledgment"
      >
        <Send size={13} aria-hidden="true" />
        <span>Submitted (Awaiting Ack)</span>
      </span>
    );
  }
  return (
    <span className="badge badge-slate" title="Saved draft handover">
      <FileEdit size={13} aria-hidden="true" />
      <span>Draft</span>
    </span>
  );
};

export const TaskStatusBadge: React.FC<{ status: string }> = ({ status }) => {
  const normalized = (status || "").toLowerCase();
  if (normalized === "completed") {
    return (
      <span className="badge badge-green">
        <CheckCircle2 size={13} aria-hidden="true" />
        <span>Completed</span>
      </span>
    );
  }
  if (normalized === "in progress") {
    return (
      <span className="badge badge-blue">
        <Wrench size={13} aria-hidden="true" />
        <span>In Progress</span>
      </span>
    );
  }
  return (
    <span className="badge badge-amber">
      <Clock size={13} aria-hidden="true" />
      <span>Pending</span>
    </span>
  );
};

export const PriorityBadge: React.FC<{ priority: string }> = ({ priority }) => {
  const normalized = (priority || "").toLowerCase();
  if (normalized === "critical") {
    return (
      <span className="badge badge-red">
        <Flame size={13} aria-hidden="true" />
        <span>Critical</span>
      </span>
    );
  }
  if (normalized === "high") {
    return (
      <span className="badge badge-amber">
        <AlertTriangle size={13} aria-hidden="true" />
        <span>High</span>
      </span>
    );
  }
  if (normalized === "medium") {
    return (
      <span className="badge badge-teal">
        <Info size={13} aria-hidden="true" />
        <span>Medium</span>
      </span>
    );
  }
  return (
    <span className="badge badge-slate">
      <CheckCircle2 size={13} aria-hidden="true" />
      <span>Low</span>
    </span>
  );
};

export const EquipmentStatusBadge: React.FC<{ status: string }> = ({
  status,
}) => {
  if (status === "OPERATIONAL") {
    return (
      <span className="badge badge-green">
        <CheckCircle2 size={13} aria-hidden="true" />
        <span>All Systems Operational</span>
      </span>
    );
  }
  if (status === "CRITICAL_FAULT") {
    return (
      <span className="badge badge-red">
        <ShieldAlert size={13} aria-hidden="true" />
        <span>Critical Fault / Grounded</span>
      </span>
    );
  }
  if (status === "MAINTENANCE_REQUIRED") {
    return (
      <span className="badge badge-amber">
        <Wrench size={13} aria-hidden="true" />
        <span>Maintenance Required</span>
      </span>
    );
  }
  return (
    <span className="badge badge-amber">
      <AlertTriangle size={13} aria-hidden="true" />
      <span>Minor Issue</span>
    </span>
  );
};
