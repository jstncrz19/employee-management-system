export function getErrorMessage(error, fallback) {
  const detail = error?.response?.data?.detail;

  if (typeof detail === "string" && detail.trim()) {
    return detail;
  }

  if (Array.isArray(detail)) {
    const messages = detail
      .map((item) =>
        typeof item?.msg === "string" && item.msg.trim() ? item.msg : null
      )
      .filter(Boolean);

    if (messages.length > 0) {
      return messages.join("; ");
    }
  }

  return fallback;
}

export default getErrorMessage;