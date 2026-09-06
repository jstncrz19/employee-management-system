import { useEffect, useState } from "react";

import api from "../services/api";
import Navbar from "../components/Navbar";

function AdminDashboard() {
  const [summary, setSummary] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    const fetchDashboardData = async () => {
      try {
        const response = await api.get("/dashboard/summary");
        setSummary(response.data);
      } catch (requestError) {
        setError(
          requestError.response?.data?.detail ||
            "Unable to load dashboard."
        );
      }
    };

    fetchDashboardData();
  }, []);

  if (!summary && !error) return <p>Loading dashboard...</p>;

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
        {error && <div className="error">{error}</div>}
        {summary && (
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
        )}
      </main>
    </div>
  );
}

export default AdminDashboard;
