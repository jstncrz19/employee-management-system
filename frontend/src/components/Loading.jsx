function Loading({ message = "Loading..." }) {
  return (
    <div className="status-state">
      <p>{message}</p>
    </div>
  );
}

export default Loading;