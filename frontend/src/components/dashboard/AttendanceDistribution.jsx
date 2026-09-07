const SEGMENT_TONE = {
  present: "tone-success",
  on_leave: "tone-warning",
  absent: "tone-danger",
};

const SEGMENT_LABEL = {
  present: "Present",
  on_leave: "On Leave",
  absent: "Absent",
};

function AttendanceDistribution({ present = 0, onLeave = 0, absent = 0 }) {
  const total = present + onLeave + absent;

  const segments = [
    { key: "present", value: present },
    { key: "on_leave", value: onLeave },
    { key: "absent", value: absent },
  ];

  const pct = (value) => (total > 0 ? Math.round((value / total) * 100) : 0);

  return (
    <div className="dist">
      <div className="dist-bar" role="img" aria-label="Attendance distribution">
        {total === 0 ? (
          <span className="dist-empty" />
        ) : (
          segments.map((segment) =>
            segment.value > 0 ? (
              <span
                key={segment.key}
                className={`dist-segment ${SEGMENT_TONE[segment.key]}`}
                style={{ width: `${pct(segment.value)}%` }}
              />
            ) : null
          )
        )}
      </div>

      <div className="dist-legend">
        {segments.map((segment) => (
          <div className="dist-legend-item" key={segment.key}>
            <span
              className={`dist-dot ${SEGMENT_TONE[segment.key]}`}
            />
            <span className="dist-legend-text">
              {SEGMENT_LABEL[segment.key]}
            </span>
            <span className="dist-legend-value">
              {segment.value}
              <span className="dist-legend-pct">
                {total > 0 ? ` (${pct(segment.value)}%)` : ""}
              </span>
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}

export default AttendanceDistribution;