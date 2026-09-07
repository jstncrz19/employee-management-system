import { useCallback, useEffect, useState } from "react";

import AppShell from "../components/layout/AppShell";
import Loading from "../components/Loading";
import EmptyState from "../components/EmptyState";
import ErrorState from "../components/ErrorState";
import StatusBadge from "../components/StatusBadge";
import PageHeader from "../components/PageHeader";
import LeaveBalances from "../components/LeaveBalances";
import LeaveCard from "../components/LeaveCard";
import api from "../services/api";
import { getErrorMessage } from "../utils/errorMessage";
import {
  formatDisplayDate,
  formatDisplayTime,
} from "../utils/formatters";

function Dashboard() {
  const [dashboard, setDashboard] = useState(null);
  const [loadError, setLoadError] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [actionMessage, setActionMessage] = useState("");
  const [actionLoading, setActionLoading] = useState(false);
  const [reloadToken, setReloadToken] = useState(0);

  const fetchDashboard = useCallback(async (showLoading = true) => {
    if (showLoading) {
      setLoading(true);
    }
    setLoadError("");

    try {
      const response = await api.get("/dashboard/me");
      setDashboard(response.data);
    } catch (requestError) {
      setLoadError(
        getErrorMessage(requestError, "Unable to load the dashboard.")
      );
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    const requestTimer = setTimeout(() => {
      fetchDashboard();
    }, 0);

    return () => clearTimeout(requestTimer);
  }, [fetchDashboard, reloadToken]);

  const handleRetry = () => {
    setReloadToken((token) => token + 1);
  };

  const handleAttendanceAction = async (action) => {
    setError("");
    setActionMessage("");
    setActionLoading(true);

    try {
      await api.post(`/attendance/${action}`);

      setActionMessage(
        action === "check-in"
          ? "You have successfully checked in."
          : "You have successfully checked out."
      );

      await fetchDashboard(false);
    } catch (requestError) {
      setError(
        getErrorMessage(requestError, "Unable to update attendance.")
      );
    } finally {
      setActionLoading(false);
    }
  };

  return (
    <AppShell>
      <main className="page-container">
        <PageHeader
          title="Dashboard"
          subtitle="Your attendance, leave balances, and upcoming time off."
        />

        {error && <div className="error">{error}</div>}
        {actionMessage && <div className="success">{actionMessage}</div>}

        {loading ? (
          <Loading message="Loading your dashboard..." />
        ) : loadError ? (
          <ErrorState
            message={loadError}
            onRetry={handleRetry}
          />
        ) : (
          <div className="dashboard-stack">
            <div className="dashboard-two-col">
              <section className="self-checkin-card">
                <h2>Today&apos;s Attendance</h2>

                {dashboard.attendance_today ? (
                  <div className="checkin-details">
                    <div className="checkin-row">
                      <span className="checkin-label">Date</span>
                      <span>
                        {formatDisplayDate(
                          dashboard.attendance_today.date
                        )}
                      </span>
                    </div>

                    <div className="checkin-row">
                      <span className="checkin-label">Time In</span>
                      <span>
                        {dashboard.attendance_today.time_in
                          ? formatDisplayTime(
                              dashboard.attendance_today.time_in
                            )
                          : "Not checked in"}
                      </span>
                    </div>

                    <div className="checkin-row">
                      <span className="checkin-label">Time Out</span>
                      <span>
                        {dashboard.attendance_today.time_out
                          ? formatDisplayTime(
                              dashboard.attendance_today.time_out
                            )
                          : "Not checked out"}
                      </span>
                    </div>

                    <div className="checkin-row">
                      <span className="checkin-label">Status</span>
                      <StatusBadge
                        status={dashboard.attendance_today.status}
                      />
                    </div>

                    {!dashboard.attendance_today.time_out && (
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

              <section>
                <h2>Leave Balances</h2>
                <LeaveBalances
                  balances={dashboard.leave_balances}
                  emptyMessage="No leave balances yet."
                />
              </section>
            </div>

            <div className="dashboard-two-col">
              <section>
                <h2>Pending Leave Requests</h2>

                {dashboard.pending_leaves.length > 0 ? (
                  <div className="record-stack">
                    {dashboard.pending_leaves.map((leave) => (
                      <LeaveCard leave={leave} key={leave.id} />
                    ))}
                  </div>
                ) : (
                  <EmptyState message="No pending leave requests." />
                )}
              </section>

              <section>
                <h2>Upcoming Leaves</h2>

                {dashboard.upcoming_leaves.length > 0 ? (
                  <div className="record-stack">
                    {dashboard.upcoming_leaves.map((leave) => (
                      <LeaveCard leave={leave} key={leave.id} />
                    ))}
                  </div>
                ) : (
                  <EmptyState message="No upcoming leaves." />
                )}
              </section>
            </div>

            <section>
              <h2>Recent Attendance</h2>

              {dashboard.recent_attendance.length > 0 ? (
                <ul className="activity-list">
                  {dashboard.recent_attendance.map((attendance) => (
                    <li
                      className="activity-item"
                      key={attendance.date}
                    >
                      <div className="activity-item-main">
                        <span className="activity-item-date">
                          {formatDisplayDate(attendance.date)}
                        </span>
                        <span className="activity-item-times">
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
                <EmptyState message="No recent attendance records." />
              )}
            </section>
          </div>
        )}
      </main>
    </AppShell>
  );
}

export default Dashboard;