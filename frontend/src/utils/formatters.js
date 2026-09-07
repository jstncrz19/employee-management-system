const MONTHS = [
  "Jan", "Feb", "Mar", "Apr", "May", "Jun",
  "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
];

function toInt(value) {
  return Number.parseInt(value, 10);
}

export function formatLeaveType(leaveType) {
  if (!leaveType) {
    return "—";
  }

  const text = String(leaveType).replace(/_/g, " ").trim();

  if (!text) {
    return "—";
  }

  return text.charAt(0).toUpperCase() + text.slice(1);
}

export function formatDisplayDate(value) {
  if (!value) {
    return "—";
  }

  const match = /^(\d{4})-(\d{1,2})-(\d{1,2})/.exec(String(value));

  if (!match) {
    const parsed = new Date(value);

    if (Number.isNaN(parsed.getTime())) {
      return String(value);
    }

    return `${MONTHS[parsed.getMonth()]} ${parsed.getDate()}, ${parsed.getFullYear()}`;
  }

  const year = toInt(match[1]);
  const month = toInt(match[2]);
  const day = toInt(match[3]);

  return `${MONTHS[month - 1]} ${day}, ${year}`;
}

export function formatDisplayTime(value) {
  if (!value) {
    return "—";
  }

  const match = /^(\d{1,2}):(\d{2})/.exec(String(value));

  if (!match) {
    return String(value);
  }

  let hours = toInt(match[1]);
  const minutes = toInt(match[2]);
  const period = hours >= 12 ? "PM" : "AM";

  hours = hours % 12;

  if (hours === 0) {
    hours = 12;
  }

  return `${hours}:${String(minutes).padStart(2, "0")} ${period}`;
}

export function formatDisplayDateTime(value) {
  if (!value) {
    return "—";
  }

  const parts = /^(\d{4}-\d{2}-\d{2})[T\s](\d{2}:\d{2})?.{0,}/.exec(
    String(value)
  );

  if (!parts) {
    return formatDisplayDate(value);
  }

  const date = formatDisplayDate(parts[1]);

  if (!parts[2]) {
    return date;
  }

  return `${date} · ${formatDisplayTime(parts[2])}`;
}

export function formatDisplayDateRange(startDate, endDate) {
  const start = formatDisplayDate(startDate);
  const end = formatDisplayDate(endDate);

  if (start === end) {
    return start;
  }

  return `${start} – ${end}`;
}

export function formatLeaveDuration(startDate, endDate) {
  const parseDate = (value) => {
    if (!value) {
      return null;
    }

    const match = /^(\d{4})-(\d{1,2})-(\d{1,2})/.exec(String(value));

    if (!match) {
      return null;
    }

    return new Date(toInt(match[1]), toInt(match[2]) - 1, toInt(match[3]));
  };

  const start = parseDate(startDate);
  const end = parseDate(endDate);

  if (!start || !end) {
    return null;
  }

  const days = Math.round((end - start) / 86400000) + 1;

  if (days <= 1) {
    return days === 1 ? "1 day" : `${days} days`;
  }

  return `${days} days`;
}