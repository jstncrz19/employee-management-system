import { useEffect, useState } from "react";

import api from "../services/api";
import Navbar from "../components/Navbar";

function AdminDashboard() {
  const [summary, setSummary] = useState(null);
  const [dashboard, setDashboard] = useState(null);

  const [error, setError] = useState("");
  const [actionMessage, setActionMessage] = useState("");
  const [actionLoading, setActionLoading] = useState(false);

  useEffect(() => {
    const fetchDashboardData = async () => {
      try {
        const [summaryResponse, dashboardResponse] =
          await Promise.all([
            api.get("/dashboard/summary"),
            api.get("/dashboard/me"),
          ]);

        setSummary(summaryResponse.data);
        setDashboard(dashboardResponse.data);
      } catch (error) {
        setError(
          error.response?.data?.detail ||
            "Unable to load dashboard."
        );
      }
    };

    fetchDashboardData();
  }, []);

  const handleAttendanceAction = async (action) => {
    setError("");
    setActionMessage("");
    setActionLoading(true);

    try {
      const response = await api.post(`/attendance/${action}`);

      setActionMessage(
        action === "check-in"
          ? "You have successfully checked in."
          : "You have successfully checked out."
      );

      setDashboard((currentDashboard) => ({
        ...currentDashboard,
        attendance_today: {
          date: response.data.date,
          time_in: response.data.time_in,
          time_out: response.data.time_out,
          status: response.data.status,
        },
      }));
    } catch (error) {
      setError(
        error.response?.data?.detail ||
          "Unable to update attendance."
      );
    } finally {
      setActionLoading(false);
    }
  };

  if (error && (!summary || !dashboard)) {
    return (
      <div>
        <Navbar />

        <main className="page-container">
          <h1>Admin Dashboard</h1>
          <div className="error">{error}</div>
        </main>
      </div>
    );
  }

  if (!summary || !dashboard) {
    return <p>Loading dashboard...</p>;
  }

  const cards = [
    {
      label: "Total Employees",
      value: summary.total_employees,
    },
    {
      label: "Active Employees",
      value: summary.active_employees,
    },
    {
      label: "Present Today",
      value: summary.present_today,
    },
    {
      label: "Absent Today",
      value: summary.absent_today,
    },
    {
      label: "On Leave Today",
      value: summary.on_leave_today,
    },
    {
      label: "Pending Leave Requests",
      value: summary.pending_leave_requests,
    },
  ];

  return (
    <div>
      <Navbar />

      <main className="page-container">
        <h1>Admin Dashboard</h1>

        {error && <div className="error">{error}</div>}
        {actionMessage && (
          <div className="success">{actionMessage}</div>
        )}

        <section>
          <h2>Company Overview</h2>

          <div className="dashboard-cards">
            {cards.map((card) => (
              <div
                className="dashboard-card"
                key={card.label}
              >
                <h2>{card.value}</h2>
                <p>{card.label}</p>
              </div>
            ))}
          </div>
        </section>

        <section>
          <h2>My Attendance</h2>

          {dashboard.attendance_today ? (
            <div>
              <p>
                Date: {dashboard.attendance_today.date}
              </p>

              <p>
                Time In:{" "}
                {dashboard.attendance_today.time_in ||
                  "Not checked in"}
              </p>

              <p>
                Time Out:{" "}
                {dashboard.attendance_today.time_out ||
                  "Not checked out"}
              </p>

              <p>
                Status: {dashboard.attendance_today.status}
              </p>

              {!dashboard.attendance_today.time_out && (
                <button
                  onClick={() =>
                    handleAttendanceAction("check-out")
                  }
                  disabled={actionLoading}
                >
                  {actionLoading
                    ? "Processing..."
                    : "Check Out"}
                </button>
              )}
            </div>
          ) : (
            <div>
              <p>No attendance recorded today.</p>

              <button
                onClick={() =>
                  handleAttendanceAction("check-in")
                }
                disabled={actionLoading}
              >
                {actionLoading
                  ? "Processing..."
                  : "Check In"}
              </button>
            </div>
          )}
        </section>

        <section>
          <h2>My Leave Balances</h2>

          {dashboard.leave_balances.length > 0 ? (
            <ul>
              {dashboard.leave_balances.map((balance) => (
                <li key={balance.leave_type}>
                  <strong>{balance.leave_type}</strong>
                  {" — "}
                  {balance.remaining_days} remaining
                </li>
              ))}
            </ul>
          ) : (
            <p>No leave balances found.</p>
          )}
        </section>

        <section>
          <h2>My Pending Leave Requests</h2>

          {dashboard.pending_leaves.length > 0 ? (
            <ul>
              {dashboard.pending_leaves.map((leave) => (
                <li key={leave.id}>
                  {leave.leave_type} — {leave.start_date} to{" "}
                  {leave.end_date}
                </li>
              ))}
            </ul>
          ) : (
            <p>No pending leave requests.</p>
          )}
        </section>

        <section>
          <h2>My Upcoming Leaves</h2>

          {dashboard.upcoming_leaves.length > 0 ? (
            <ul>
              {dashboard.upcoming_leaves.map((leave) => (
                <li key={leave.id}>
                  {leave.leave_type} — {leave.start_date} to{" "}
                  {leave.end_date}
                </li>
              ))}
            </ul>
          ) : (
            <p>No upcoming leaves.</p>
          )}
        </section>

        <section>
          <h2>My Recent Attendance</h2>

          {dashboard.recent_attendance.length > 0 ? (
            <ul>
              {dashboard.recent_attendance.map(
                (attendance) => (
                  <li key={attendance.date}>
                    {attendance.date} —{" "}
                    {attendance.time_in || "No time in"} →{" "}
                    {attendance.time_out || "No time out"} —{" "}
                    {attendance.status}
                  </li>
                )
              )}
            </ul>
          ) : (
            <p>No recent attendance records.</p>
          )}
        </section>
      </main>
    </div>
  );
}

export default AdminDashboard;