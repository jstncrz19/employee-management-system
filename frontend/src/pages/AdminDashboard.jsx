import { useCallback, useEffect, useState } from "react";

import api from "../services/api";
import Navbar from "../components/Navbar";
import Loading from "../components/Loading";
import ErrorState from "../components/ErrorState";
import StatusBadge from "../components/StatusBadge";
import { getErrorMessage } from "../utils/errorMessage";

function formatLocalDate(date) {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");

  return `${year}-${month}-${day}`;
}

function AdminDashboard() {
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState("");
  const [reloadToken, setReloadToken] = useState(0);

  const [attendanceToday, setAttendanceToday] = useState(null);
  const [attendanceLoading, setAttendanceLoading] = useState(true);
  const [attendanceError, setAttendanceError] = useState("");
  const [attendanceReloadToken, setAttendanceReloadToken] = useState(0);
  const [actionMessage, setActionMessage] = useState("");
  const [actionError, setActionError] = useState("");
  const [actionLoading, setActionLoading] = useState(false);

  const fetchDashboardData = useCallback(async (showLoading = true) => {
    if (showLoading) {
      setLoading(true);
    }
    setLoadError("");

    try {
      const response = await api.get("/dashboard/summary");
      setSummary(response.data);
    } catch (requestError) {
      setLoadError(
        getErrorMessage(requestError, "Unable to load the dashboard.")
      );
    } finally {
      setLoading(false);
    }
  }, []);

  const fetchMyAttendance = useCallback(async () => {
    setAttendanceLoading(true);
    setAttendanceError("");

    try {
      const response = await api.get("/attendance/me");
      const today = formatLocalDate(new Date());
      const todayRecord =
        response.data.find((record) => record.date === today) || null;

      setAttendanceToday(todayRecord);
    } catch (requestError) {
      setAttendanceError(
        getErrorMessage(requestError, "Unable to load today's attendance.")
      );
    } finally {
      setAttendanceLoading(false);
    }
  }, []);

  useEffect(() => {
    const requestTimer = setTimeout(() => {
      fetchDashboardData();
    }, 0);

    return () => clearTimeout(requestTimer);
  }, [fetchDashboardData, reloadToken]);

  useEffect(() => {
    const requestTimer = setTimeout(() => {
      fetchMyAttendance();
    }, 0);

    return () => clearTimeout(requestTimer);
  }, [fetchMyAttendance, attendanceReloadToken]);

  const handleRetry = () => {
    setReloadToken((token) => token + 1);
  };

  const handleAttendanceRetry = () => {
    setAttendanceReloadToken((token) => token + 1);
  };

  const handleAttendanceAction = async (action) => {
    setActionError("");
    setActionMessage("");
    setActionLoading(true);

    try {
      const response = await api.post(`/attendance/${action}`);

      setActionMessage(
        action === "check-in"
          ? "You have successfully checked in."
          : "You have successfully checked out."
      );

      setAttendanceToday({
        date: response.data.date,
        time_in: response.data.time_in,
        time_out: response.data.time_out,
        status: response.data.status,
      });

      await fetchDashboardData(false);
    } catch (requestError) {
      setActionError(
        getErrorMessage(requestError, "Unable to update attendance.")
      );
    } finally {
      setActionLoading(false);
    }
  };

  const cards = summary
    ? [
        { label: "Total Employees", value: summary.total_employees },
        { label: "Active Employees", value: summary.active_employees },
        { label: "Present Today", value: summary.present_today },
        { label: "Absent Today", value: summary.absent_today },
        { label: "On Leave Today", value: summary.on_leave_today },
        {
          label: "Pending Leave Requests",
          value: summary.pending_leave_requests,
        },
      ]
    : [];

  return (
    <div>
      <Navbar />
      <main className="page-container">
        <h1>Admin Dashboard</h1>

        {actionError && (
          <div className="error">{actionError}</div>
        )}

        {actionMessage && (
          <div className="success">{actionMessage}</div>
        )}

        <section>
          <h2>Today's Attendance</h2>

          {attendanceLoading ? (
            <Loading message="Loading today's attendance..." />
          ) : attendanceError ? (
            <div>
              <div className="error">{attendanceError}</div>
              <button
                className="btn-primary"
                onClick={handleAttendanceRetry}
              >
                Retry
              </button>
            </div>
          ) : attendanceToday ? (
            <div>
              <p>Date: {attendanceToday.date}</p>
              <p>
                Time In:{" "}
                {attendanceToday.time_in || "Not checked in"}
              </p>
              <p>
                Time Out:{" "}
                {attendanceToday.time_out || "Not checked out"}
              </p>
              <p>Status: <StatusBadge status={attendanceToday.status} /></p>

              {!attendanceToday.time_out && (
                <button
                  className="btn-primary"
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
                className="btn-primary"
                onClick={() => handleAttendanceAction("check-in")}
                disabled={actionLoading}
              >
                {actionLoading ? "Processing..." : "Check In"}
              </button>
            </div>
          )}
        </section>

        {loading ? (
          <Loading message="Loading dashboard summary..." />
        ) : loadError ? (
          <ErrorState
            message={loadError}
            onRetry={handleRetry}
          />
        ) : summary ? (
          <section>
            <h2>Company Overview</h2>
            <div className="dashboard-cards">
              {cards.map((card) => (
                <div className="dashboard-card" key={card.label}>
                  <h2>{card.value}</h2>
                  <p>{card.label}</p>
                </div>
              ))}
            </div>
          </section>
        ) : null}
      </main>
    </div>
  );
}

export default AdminDashboard;