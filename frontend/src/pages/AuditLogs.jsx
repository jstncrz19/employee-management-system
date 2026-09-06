import { useEffect, useState } from "react";

import api from "../services/api";
import Navbar from "../components/Navbar";

function AuditLogs() {
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const [page, setPage] = useState(1);
  const [pages, setPages] = useState(0);
  const [total, setTotal] = useState(0);

  const limit = 10;

  const fetchLogs = async (currentPage = page) => {
    setLoading(true);
    setError("");

    try {
      const response = await api.get("/audit-logs", {
        params: {
          page: currentPage,
          limit: limit,
        },
      });

      setLogs(response.data.items);
      setPage(response.data.page);
      setPages(response.data.pages);
      setTotal(response.data.total);
    } catch (error) {
      setError(
        error.response?.data?.detail ||
          "Unable to load audit logs."
      );
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchLogs(1);
  }, []);

  const handlePrevious = () => {
    if (page > 1) {
      fetchLogs(page - 1);
    }
  };

  const handleNext = () => {
    if (page < pages) {
      fetchLogs(page + 1);
    }
  };

  if (loading) {
    return (
      <div>
        <Navbar />
        <main className="page-container">
          <p>Loading audit logs...</p>
        </main>
      </div>
    );
  }

  return (
    <div>
      <Navbar />

      <main className="page-container">
        <h1>Audit Logs</h1>

        {error && <div className="error">{error}</div>}

        {logs.length === 0 ? (
          <p>No audit logs found.</p>
        ) : (
          <>
            <table>
              <thead>
                <tr>
                  <th>User / Employee</th>
                  <th>Action</th>
                  <th>Entity</th>
                  <th>Entity ID</th>
                  <th>Details</th>
                  <th>Created</th>
                </tr>
              </thead>

              <tbody>
                {logs.map((log) => (
                  <tr key={log.id}>
                    <td>
                      {log.employee_name ? (
                        <div>
                          <strong>{log.employee_name}</strong>
                          <br />
                          <small>{log.user_email}</small>
                        </div>
                      ) : (
                        <div>
                          <strong>Admin</strong>
                          <br />
                          <small>{log.user_email}</small>
                        </div>
                      )}
                    </td>

                    <td>{log.action}</td>

                    <td>{log.entity_type}</td>

                    <td>{log.entity_id}</td>

                    <td>{log.details || "—"}</td>

                    <td>{log.created_at}</td>
                  </tr>
                ))}
              </tbody>
            </table>

            <div>
              <p>
                Showing page {page} of {pages} — {total} total logs
              </p>

              <button
                onClick={handlePrevious}
                disabled={page <= 1}
              >
                Previous
              </button>

              {" "}

              <button
                onClick={handleNext}
                disabled={page >= pages}
              >
                Next
              </button>
            </div>
          </>
        )}
      </main>
    </div>
  );
}

export default AuditLogs;