function StatCard({ label, value, icon }) {
  return (
    <div className="stat-card">
      <div className="stat-card-body">
        <span className="stat-card-label">{label}</span>
        <span className="stat-card-value">{value}</span>
      </div>
      {icon && (
        <span className="stat-card-icon material-symbols-outlined">
          {icon}
        </span>
      )}
    </div>
  );
}

export default StatCard;