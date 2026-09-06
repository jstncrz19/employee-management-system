const STATUS_STYLES = {
  active: "badge badge-success",
  approved: "badge badge-success",
  present: "badge badge-success",
  pending: "badge badge-warning",
  on_leave: "badge badge-warning",
  inactive: "badge badge-neutral",
  cancelled: "badge badge-neutral",
  resigned: "badge badge-neutral",
  absent: "badge badge-danger",
  rejected: "badge badge-danger",
  terminated: "badge badge-danger",
};

function formatStatus(status) {
  if (!status) {
    return "—";
  }

  return status
    .replace(/_/g, " ")
    .toLowerCase()
    .replace(/\b[a-z]/g, (character) => character.toUpperCase());
}

function StatusBadge({ status }) {
  const className =
    STATUS_STYLES[status] || "badge badge-neutral";

  return <span className={className}>{formatStatus(status)}</span>;
}

export default StatusBadge;