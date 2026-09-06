function ErrorState({ message, onRetry, retryLabel = "Retry" }) {
  return (
    <div className="status-state status-state-error">
      <p>{message}</p>
      {onRetry && (
        <button type="button" onClick={onRetry}>
          {retryLabel}
        </button>
      )}
    </div>
  );
}

export default ErrorState;