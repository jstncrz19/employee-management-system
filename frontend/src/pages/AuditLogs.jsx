import { useCallback, useEffect, useState } from "react";

import api from "../services/api";
import Navbar from "../components/Navbar";
import Loading from "../components/Loading";
import EmptyState from "../components/EmptyState";
import ErrorState from "../components/ErrorState";
import { getErrorMessage } from "../utils/errorMessage";

function AuditLogs() {
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState("");

  const [page, setPage] = useState(1);
  const [pages, setPages] = useState(0);
  const [total, setTotal] = useState(0);

  const limit = 10;

  const fetchLogs = useCallback(async (currentPage = page) => {
    setLoading(true);
    setLoadError("");

    try {
      const response = await api.get("/audit-logs", {
        params: {
          page: currentPage,
          limit,
        },
      });

      setLogs(response.data.items);
      setPage(response.data.page);
      setPages(response.data.pages);
      setTotal(response.data.total);
    } catch (error) {
      setLoadError(
        getErrorMessage(error, "Unable to load audit logs.")
      );
    } finally {
      setLoading(false);
    }
  }, [page]);

  useEffect(() => {
    const requestTimer = setTimeout(() => {
      fetchLogs(page);
    }, 0);

    return () => clearTimeout(requestTimer);
  }, [fetchLogs, page]);

  const handlePrevious = () => {
    if (page > 1) {
      setPage((current) => current - 1);
    }
  };

  const handleNext = () => {
    if (page < pages) {
      setPage((current) => current + 1);
    }
  };

  return (
    <div>
      <Navbar />

      <main className="page-container">
        <h1>Audit Logs</h1>

        {loading ? (
          <Loading message="Loading audit logs..." />
        ) : loadError ? (
          <ErrorState
            message={loadError}
            onRetry={() => fetchLogs(page)}
          />
        ) : logs.length === 0 ? (
          <EmptyState message="No audit logs yet." />
        ) : (
          <>
            <div className="table-wrapper">
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
            </div>

            <div className="toolbar">
              <p>
                Showing page {page} of {pages} — {total} total logs
              </p>

              <button
                className="btn-secondary"
                onClick={handlePrevious}
                disabled={page <= 1}
              >
                Previous
              </button>

              {" "}

              <button
                className="btn-secondary"
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
