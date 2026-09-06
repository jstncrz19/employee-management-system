import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

import Navbar from "../components/Navbar";
import api from "../services/api";
import { useAuth } from "../hooks/useAuth";

function Dashboard() {
  const [dashboard, setDashboard] = useState(null);
  const [error, setError] = useState("");
  const [actionMessage, setActionMessage] = useState("");
  const [actionLoading, setActionLoading] = useState(false);

  const navigate = useNavigate();
  const { logout } = useAuth();

  useEffect(() => {
    const fetchDashboard = async () => {
      try {
        const response = await api.get("/dashboard/me");
        setDashboard(response.data);
      } catch (error) {
        setError(
          error.response?.data?.detail ||
            "Unable to load dashboard."
        );
      }
    };

    fetchDashboard();
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

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  if (error) {
    return (
      <div>
        <h1>Dashboard</h1>
        <p>{error}</p>
        <button onClick={handleLogout}>Logout</button>
      </div>
    );
  }

  if (!dashboard) {
    return <p>Loading dashboard...</p>;
  }

  return (
    <div>
        <Navbar />

        <main className="page-container">
          <h1>Employee Dashboard</h1>

          <section>
            <h2>Today's Attendance</h2>

            {dashboard.attendance_today ? (
              <div>
                <p>
                  Date: {dashboard.attendance_today.date}
                </p>
                <p>
                  Time In:{" "}
                  {dashboard.attendance_today.time_in || "Not checked in"}
                </p>
                <p>
                  Time Out:{" "}
                  {dashboard.attendance_today.time_out || "Not checked out"}
                </p>
                <p>
                  Status: {dashboard.attendance_today.status}
                </p>

                {!dashboard.attendance_today.time_out && (
                  <button
                    onClick={() => handleAttendanceAction("check-out")}
                    disabled={actionLoading}
                  >
                    {actionLoading ? "Processing..." : "Check Out"}
                  </button>
                )}
              </div>
            ) : (
              <div>
                <p>No attendance recorded today.</p>
                <button
                  onClick={() => handleAttendanceAction("check-in")}
                  disabled={actionLoading}
                >
                  {actionLoading ? "Processing..." : "Check In"}
                </button>
              </div>
            )}

            {actionMessage && <p>{actionMessage}</p>}
          </section>

          <section>
            <h2>Leave Balances</h2>

            {dashboard.leave_balances.length > 0 ? (
              <ul>
                {dashboard.leave_balances.map((balance) => (
                  <li key={balance.leave_type}>
                    {balance.leave_type}:{" "}
                    {balance.remaining_days} remaining
                  </li>
                ))}
              </ul>
            ) : (
              <p>No leave balances found.</p>
            )}
          </section>

          <section>
            <h2>Pending Leave Requests</h2>

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
            <h2>Upcoming Leaves</h2>

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
            <h2>Recent Attendance</h2>

            {dashboard.recent_attendance.length > 0 ? (
              <ul>
                {dashboard.recent_attendance.map((attendance) => (
                  <li key={attendance.date}>
                    {attendance.date} —{" "}
                    {attendance.time_in || "No time in"} →{" "}
                    {attendance.time_out || "No time out"} —{" "}
                    {attendance.status}
                  </li>
                ))}
              </ul>
            ) : (
              <p>No recent attendance records.</p>
            )}
          </section>
          
        </main>
    </div>
  );
}

export default Dashboard;