import StatusBadge from "./StatusBadge";
import {
  formatDisplayDateRange,
  formatLeaveDuration,
  formatLeaveType,
} from "../utils/formatters";

const LEAVE_TYPE_ICONS = {
  vacation: "beach_access",
  sick: "medical_services",
  emergency: "warning",
  other: "event_available",
};

function LeaveCard({ leave, children }) {
  const duration = formatLeaveDuration(leave.start_date, leave.end_date);

  return (
    <div className="leave-card">
      <div className="leave-card-head">
        <span className="leave-card-title">
          <span className="leave-card-icon">
            <span className="material-symbols-outlined">
              {LEAVE_TYPE_ICONS[leave.leave_type] || "event_available"}
            </span>
          </span>
          <span>{formatLeaveType(leave.leave_type)}</span>
        </span>

        <StatusBadge status={leave.status} />
      </div>

      <div className="leave-card-row">
        <span className="checkin-label">Dates</span>
        <span>
          {formatDisplayDateRange(leave.start_date, leave.end_date)}
        </span>
      </div>

      <div className="leave-card-row">
        <span className="checkin-label">Duration</span>
        <span>{duration || "—"}</span>
      </div>

      {leave.reason && (
        <div className="leave-card-note">
          <span className="checkin-label">Reason</span>
          <p>{leave.reason}</p>
        </div>
      )}

      {children && (
        <div className="leave-card-actions">{children}</div>
      )}
    </div>
  );
}

export default LeaveCard;