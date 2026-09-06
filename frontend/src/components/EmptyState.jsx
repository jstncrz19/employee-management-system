function EmptyState({ message, hint }) {
  return (
    <div className="status-state status-state-empty">
      <p>{message}</p>
      {hint && <p className="status-state-hint">{hint}</p>}
    </div>
  );
}

export default EmptyState;