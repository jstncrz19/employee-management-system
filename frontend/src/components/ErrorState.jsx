function ErrorState({ message, onRetry, retryLabel = "Retry" }) {
  return (
    <div className="status-state status-state-error">
      <p>{message}</p>
      {onRetry && (
        <button className="btn-primary" type="button" onClick={onRetry}>
          {retryLabel}
        </button>
      )}
    </div>
  );
}

export default ErrorState;