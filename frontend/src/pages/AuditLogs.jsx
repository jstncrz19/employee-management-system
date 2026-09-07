import { useCallback, useEffect, useState } from "react";

import api from "../services/api";
import AppShell from "../components/layout/AppShell";
import Loading from "../components/Loading";
import EmptyState from "../components/EmptyState";
import ErrorState from "../components/ErrorState";
import PageHeader from "../components/PageHeader";
import { getErrorMessage } from "../utils/errorMessage";
import { formatDisplayDateTime } from "../utils/formatters";

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
    <AppShell>
      <main className="page-container">
        <PageHeader
          title="Audit Logs"
          subtitle="A chronological record of actions performed in the system."
        />

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
            <p className="results-line">
              Page {page} of {pages} — {total} total logs
            </p>

            <div className="responsive-table">
              <div className="table-wrapper">
                <table>
                  <thead>
                    <tr>
                      <th>Date / Time</th>
                      <th>User</th>
                      <th>Action</th>
                      <th>Resource</th>
                      <th>Details</th>
                    </tr>
                  </thead>

                  <tbody>
                    {logs.map((log) => (
                      <tr key={log.id}>
                        <td data-label="Date / Time">
                          <span className="responsive-cell-value">
                            {formatDisplayDateTime(log.created_at)}
                          </span>
                        </td>

                        <td data-label="User">
                          <span className="responsive-cell-value">
                            {log.employee_name ? (
                              <div>
                                <div className="responsive-name">
                                  {log.employee_name}
                                </div>
                                <div className="muted-text">
                                  {log.user_email}
                                </div>
                              </div>
                            ) : (
                              <div>
                                <div className="responsive-name">Admin</div>
                                <div className="muted-text">
                                  {log.user_email}
                                </div>
                              </div>
                            )}
                          </span>
                        </td>

                        <td data-label="Action">
                          <span className="responsive-cell-value">
                            <span className="badge badge-neutral">
                              {log.action}
                            </span>
                          </span>
                        </td>

                        <td data-label="Resource">
                          <span className="responsive-cell-value">
                            {log.entity_type}{" "}
                            <span className="muted-text">
                              #{log.entity_id}
                            </span>
                          </span>
                        </td>

                        <td data-label="Details" className="text-cell">
                          <span className="responsive-cell-value">
                            {log.details || "—"}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </>
        )}

        <div className="toolbar">
          <button
            className="btn-secondary"
            onClick={handlePrevious}
            disabled={loading || page <= 1}
          >
            Previous
          </button>

          <span className="results-line">
            {" "}
            Page {page} of {pages}{" "}
          </span>

          <button
            className="btn-secondary"
            onClick={handleNext}
            disabled={loading || page >= pages}
          >
            Next
          </button>
        </div>
      </main>
    </AppShell>
  );
}

export default AuditLogs;