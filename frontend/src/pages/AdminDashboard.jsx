import { useCallback, useEffect, useState } from "react";

import api from "../services/api";
import Navbar from "../components/Navbar";
import Loading from "../components/Loading";
import ErrorState from "../components/ErrorState";
import { getErrorMessage } from "../utils/errorMessage";

function AdminDashboard() {
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState("");
  const [reloadToken, setReloadToken] = useState(0);

  const fetchDashboardData = useCallback(async () => {
    setLoading(true);
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

  useEffect(() => {
    const requestTimer = setTimeout(() => {
      fetchDashboardData();
    }, 0);

    return () => clearTimeout(requestTimer);
  }, [fetchDashboardData, reloadToken]);

  const handleRetry = () => {
    setReloadToken((token) => token + 1);
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