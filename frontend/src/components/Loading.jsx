function Loading({ message = "Loading..." }) {
  return (
    <div className="status-state status-state-loading">
      <p>{message}</p>
    </div>
  );
}

export default Loading;