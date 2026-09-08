import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";

import api from "../services/api";
import AppShell from "../components/layout/AppShell";
import Loading from "../components/Loading";
import ErrorState from "../components/ErrorState";
import EmptyState from "../components/EmptyState";
import StatusBadge from "../components/StatusBadge";
import StatCard from "../components/dashboard/StatCard";
import AttendanceDistribution from "../components/dashboard/AttendanceDistribution";
import { getErrorMessage } from "../utils/errorMessage";
import {
  formatDisplayDate,
  formatDisplayTime,
} from "../utils/formatters";

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

  const [recentAttendance, setRecentAttendance] = useState([]);
  const [recentAttendanceLoading, setRecentAttendanceLoading] = useState(true);
  const [recentAttendanceError, setRecentAttendanceError] = useState("");
  const [recentAttendanceReloadToken, setRecentAttendanceReloadToken] = useState(0);

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

  const fetchRecentAttendance = useCallback(async () => {
    setRecentAttendanceLoading(true);
    setRecentAttendanceError("");

    try {
      const response = await api.get("/attendance", {
        params: { page: 1, limit: 5 },
      });

      setRecentAttendance(response.data.items);
    } catch (requestError) {
      setRecentAttendanceError(
        getErrorMessage(requestError, "Unable to load recent attendance.")
      );
    } finally {
      setRecentAttendanceLoading(false);
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

  useEffect(() => {
    const requestTimer = setTimeout(() => {
      fetchRecentAttendance();
    }, 0);

    return () => clearTimeout(requestTimer);
  }, [fetchRecentAttendance, recentAttendanceReloadToken]);

  const handleRetry = () => {
    setReloadToken((token) => token + 1);
  };

  const handleAttendanceRetry = () => {
    setAttendanceReloadToken((token) => token + 1);
  };

  const handleRecentAttendanceRetry = () => {
    setRecentAttendanceReloadToken((token) => token + 1);
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

  return (
    <AppShell>
      <main className="page-container">
        <div className="page-header">
          <div>
            <h1>Dashboard</h1>
            <p className="page-subtitle">
              Overview of today&apos;s workforce activity.
            </p>
          </div>
        </div>

        {actionError && (
          <div className="error">{actionError}</div>
        )}

        {actionMessage && (
          <div className="success">{actionMessage}</div>
        )}

        {loading ? (
          <Loading message="Loading dashboard summary..." />
        ) : loadError ? (
          <ErrorState
            message={loadError}
            onRetry={handleRetry}
          />
        ) : summary ? (
          <div className="dashboard-stack">
            <section className="kpi-grid">
              <StatCard
                label="Total Employees"
                value={summary.total_employees}
                icon="group"
              />
              <StatCard
                label="Present Today"
                value={summary.present_today}
                icon="event_available"
              />
              <StatCard
                label="On Leave Today"
                value={summary.on_leave_today}
                icon="holiday_village"
              />
              <StatCard
                label="Absent Today"
                value={summary.absent_today}
                icon="person_off"
              />
            </section>

            <div className="dashboard-two-col">
              <section>
                <h2>Attendance Overview</h2>
                <AttendanceDistribution
                  present={summary.present_today}
                  onLeave={summary.on_leave_today}
                  absent={summary.absent_today}
                />
              </section>

              <section className="self-checkin-card">
                <h2>Today&apos;s Work Session</h2>

                {attendanceLoading ? (
                  <Loading message="Loading..." />
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
                  <div className="checkin-details">
                    <div className="checkin-row">
                      <span className="checkin-label">Date</span>
                      <span>
                        {formatDisplayDate(attendanceToday.date)}
                      </span>
                    </div>
                    <div className="checkin-row">
                      <span className="checkin-label">Time In</span>
                      <span>
                        {formatDisplayTime(attendanceToday.time_in) ||
                          "Not checked in"}
                      </span>
                    </div>
                    <div className="checkin-row">
                      <span className="checkin-label">Time Out</span>
                      <span>
                        {formatDisplayTime(attendanceToday.time_out) ||
                          "Not checked out"}
                      </span>
                    </div>
                    <div className="checkin-row">
                      <span className="checkin-label">Status</span>
                      <StatusBadge status={attendanceToday.status} />
                    </div>

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
                  <div className="checkin-details">
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
            </div>

            <section>
              <h2>Recent Attendance</h2>

              {recentAttendanceLoading ? (
                <Loading message="Loading recent attendance..." />
              ) : recentAttendanceError ? (
                <ErrorState
                  message={recentAttendanceError}
                  onRetry={handleRecentAttendanceRetry}
                />
              ) : recentAttendance.length > 0 ? (
                <ul className="activity-list">
                  {recentAttendance.map((attendance) => (
                    <li
                      className="activity-item"
                      key={attendance.id}
                    >
                      <div className="activity-item-main">
                        <span className="activity-item-date">
                          {attendance.employee_name ||
                            `Employee #${attendance.employee_id}`}
                        </span>
                        <span className="activity-item-times">
                          {attendance.employee_number
                            ? `#${attendance.employee_number} · `
                            : ""}
                          {formatDisplayDate(attendance.date)}
                          {" · "}
                          {attendance.time_in
                            ? formatDisplayTime(attendance.time_in)
                            : "No time in"}
                          {" → "}
                          {attendance.time_out
                            ? formatDisplayTime(attendance.time_out)
                            : "No time out"}
                        </span>
                      </div>

                      <StatusBadge status={attendance.status} />
                    </li>
                  ))}
                </ul>
              ) : (
                <EmptyState message="No attendance records found." />
              )}

              <div className="toolbar">
                <Link
                  className="link-button"
                  to="/admin/attendance"
                >
                  View All Attendance
                </Link>
              </div>
            </section>
          </div>
        ) : null}
      </main>
    </AppShell>
  );
}

export default AdminDashboard;