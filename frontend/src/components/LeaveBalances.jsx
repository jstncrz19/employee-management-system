import EmptyState from "./EmptyState";
import { LEAVE_TYPE_ICONS, formatLeaveType } from "../utils/formatters";

function LeaveBalances({
  balances,
  emptyMessage = "No leave balances available yet.",
}) {
  if (!balances || balances.length === 0) {
    return <EmptyState message={emptyMessage} />;
  }

  return (
    <div className="balance-grid">
      {balances.map((balance) => (
        <div className="balance-card" key={balance.leave_type}>
          <div className="balance-card-head">
            <span className="balance-card-icon">
              <span className="material-symbols-outlined">
                {LEAVE_TYPE_ICONS[balance.leave_type] || "event_available"}
              </span>
            </span>
            <span className="balance-card-label">
              {formatLeaveType(balance.leave_type)}
            </span>
          </div>

          <div className="balance-card-value">
            {balance.remaining_days}
          </div>

          <div className="balance-card-caption">remaining</div>

          <div className="balance-card-meta">
            <span>Total {balance.total_days}</span>
            <span>Used {balance.used_days}</span>
          </div>
        </div>
      ))}
    </div>
  );
}

export default LeaveBalances;