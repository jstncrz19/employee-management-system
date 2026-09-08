import { useCallback, useEffect, useState } from "react";

import api from "../services/api";
import AppShell from "../components/layout/AppShell";
import Loading from "../components/Loading";
import EmptyState from "../components/EmptyState";
import ErrorState from "../components/ErrorState";
import PageHeader from "../components/PageHeader";
import { getErrorMessage } from "../utils/errorMessage";
import { formatDisplayDateTime } from "../utils/formatters";

const ACTION_OPTIONS = [
  "create",
  "update",
  "deactivate",
  "register",
  "approve",
  "reject",
  "cancel",
  "check_in",
  "check_out",
];

const ENTITY_TYPE_OPTIONS = [
  "employee",
  "user",
  "attendance",
  "leave",
  "leave_balance",
];

function formatOptionLabel(value) {
  return value
    .replace(/_/g, " ")
    .toLowerCase()
    .replace(/\b[a-z]/g, (character) => character.toUpperCase());
}

function AuditLogs() {
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState("");

  const [action, setAction] = useState("");
  const [userId, setUserId] = useState("");
  const [entityType, setEntityType] = useState("");

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
          ...(action && { action }),
          ...(userId && { user_id: Number(userId) }),
          ...(entityType && { entity_type: entityType }),
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
  }, [action, entityType, page, userId]);

  useEffect(() => {
    const requestTimer = setTimeout(() => {
      fetchLogs(page);
    }, 0);

    return () => clearTimeout(requestTimer);
  }, [fetchLogs, page]);

  const resetPage = (setter) => (event) => {
    setter(event.target.value);
    if (page !== 1) setPage(1);
  };

  const clearFilters = () => {
    setAction("");
    setUserId("");
    setEntityType("");
    if (page !== 1) setPage(1);
  };

  const hasActiveFilters = Boolean(action || userId || entityType);

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

        <div className="toolbar">
          <select
            value={action}
            onChange={resetPage(setAction)}
            aria-label="Filter by action"
          >
            <option value="">All Actions</option>
            {ACTION_OPTIONS.map((option) => (
              <option key={option} value={option}>
                {formatOptionLabel(option)}
              </option>
            ))}
          </select>

          <input
            type="number"
            min="1"
            placeholder="User ID"
            value={userId}
            onChange={resetPage(setUserId)}
            aria-label="Filter by user ID"
          />

          <select
            value={entityType}
            onChange={resetPage(setEntityType)}
            aria-label="Filter by resource type"
          >
            <option value="">All Resources</option>
            {ENTITY_TYPE_OPTIONS.map((option) => (
              <option key={option} value={option}>
                {formatOptionLabel(option)}
              </option>
            ))}
          </select>

          <button
            className="btn-secondary"
            type="button"
            onClick={clearFilters}
          >
            Clear Filters
          </button>
        </div>

        {loading ? (
          <Loading message="Loading audit logs..." />
        ) : loadError ? (
          <ErrorState
            message={loadError}
            onRetry={() => fetchLogs(page)}
          />
        ) : logs.length === 0 ? (
          <EmptyState
            message={
              hasActiveFilters
                ? "No audit logs match your filters."
                : "No audit logs yet."
            }
          />
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