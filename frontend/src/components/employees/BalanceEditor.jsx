import Loading from "../Loading";
import EmptyState from "../EmptyState";
import { formatLeaveType } from "../../utils/formatters";

function BalanceEditor({
  employee,
  balances,
  loading,
  updatingType,
  onBalanceChange,
  onBalanceUpdate,
  onClose,
}) {
  return (
    <section>
      <div className="leave-card-note-header">
        <h2>
          Leave Balances —{" "}
          {employee.first_name}{" "}
          {employee.last_name}
        </h2>

        <button
          className="btn-secondary btn-sm"
          type="button"
          onClick={onClose}
        >
          Close
        </button>
      </div>

      {loading ? (
        <Loading message="Loading leave balances..." />
      ) : balances.length === 0 ? (
        <EmptyState message="No leave balances set up for this employee yet." />
      ) : (
        <div className="balance-editor-grid">
          {balances.map((balance) => (
            <div
              className="balance-editor-card"
              key={balance.leave_type}
            >
              <h3>{formatLeaveType(balance.leave_type)}</h3>

              <div className="balance-editor-field">
                <label htmlFor={`balance-${balance.leave_type}`}>
                  Total Days
                </label>

                <input
                  id={`balance-${balance.leave_type}`}
                  type="number"
                  min="0"
                  max="365"
                  value={balance.total_days}
                  onChange={(event) =>
                    onBalanceChange(
                      balance.leave_type,
                      event.target.value
                    )
                  }
                />
              </div>

              <div className="balance-editor-stats">
                <span>Used: {balance.used_days}</span>
                <span>
                  Remaining: {balance.remaining_days}
                </span>
              </div>

              <button
                className="btn-primary btn-sm"
                type="button"
                onClick={() => onBalanceUpdate(balance)}
                disabled={updatingType === balance.leave_type}
              >
                {updatingType === balance.leave_type
                  ? "Updating..."
                  : "Update Balance"}
              </button>
            </div>
          ))}
        </div>
      )}
    </section>
  );
}

export default BalanceEditor;
