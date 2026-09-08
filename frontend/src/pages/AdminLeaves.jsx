import { useCallback, useEffect, useState } from "react";

import api from "../services/api";
import AppShell from "../components/layout/AppShell";
import Loading from "../components/Loading";
import EmptyState from "../components/EmptyState";
import ErrorState from "../components/ErrorState";
import StatusBadge from "../components/StatusBadge";
import PageHeader from "../components/PageHeader";
import { getErrorMessage } from "../utils/errorMessage";
import {
  formatDisplayDateRange,
  formatLeaveType,
} from "../utils/formatters";

const LIMIT = 10;

function AdminLeaves() {
  const [leaves, setLeaves] = useState([]);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState("");
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [searchInput, setSearchInput] = useState("");
  const [search, setSearch] = useState("");
  const [status, setStatus] = useState("");
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const [page, setPage] = useState(1);
  const [pages, setPages] = useState(0);
  const [total, setTotal] = useState(0);
  const [actionPending, setActionPending] = useState(null);

  const fetchLeaves = useCallback(async (requestedPage = page) => {
    setLoading(true);
    setLoadError("");
    try {
      const response = await api.get("/leaves", {
        params: {
          page: requestedPage,
          limit: LIMIT,
          ...(search && { search }),
          ...(status && { status }),
          ...(startDate && { start_date: startDate }),
          ...(endDate && { end_date: endDate }),
        },
      });
      setLeaves(response.data.items);
      setPage(response.data.page);
      setPages(response.data.pages);
      setTotal(response.data.total);
    } catch (requestError) {
      setLoadError(
        getErrorMessage(requestError, "Unable to load leave requests.")
      );
    } finally {
      setLoading(false);
    }
  }, [endDate, page, search, startDate, status]);

  useEffect(() => {
    const requestTimer = setTimeout(() => {
      fetchLeaves(page);
    }, 0);
    return () => clearTimeout(requestTimer);
  }, [fetchLeaves, page]);

  const applyFilters = () => {
    setSearch(searchInput.trim());
    if (page !== 1) setPage(1);
  };

  const clearFilters = () => {
    setSearchInput("");
    setSearch("");
    setStatus("");
    setStartDate("");
    setEndDate("");
    if (page !== 1) setPage(1);
  };

  const handleAction = async (leaveId, action) => {
    if (action === "reject") {
      const confirmed = window.confirm("Reject this leave request?");
      if (!confirmed) return;
    }

    setError("");
    setMessage("");
    setActionPending({ leaveId, action });
    try {
      await api.patch(`/leaves/${leaveId}/${action}`);
      setMessage(
        action === "approve"
          ? "Leave request approved."
          : "Leave request rejected."
      );
      await fetchLeaves();
    } catch (requestError) {
      setError(
        getErrorMessage(requestError, "Unable to update leave request.")
      );
    } finally {
      setActionPending(null);
    }
  };

  const hasActiveFilters = Boolean(
    search.trim() || status || startDate || endDate
  );

  const isPending = (leaveId, action) =>
    actionPending?.leaveId === leaveId &&
    actionPending.action === action;

  return (
    <AppShell>
      <main className="page-container">
        <PageHeader
          title="Leave Requests"
          subtitle="Review requests and approve or reject time off."
        />

        {error && <div className="error">{error}</div>}
        {message && <div className="success">{message}</div>}

        <div className="toolbar">
          <input
            type="search"
            placeholder="Search name, number, or email"
            value={searchInput}
            onChange={(event) => setSearchInput(event.target.value)}
            onKeyDown={(event) => {
              if (event.key === "Enter") applyFilters();
            }}
          />

          <select
            value={status}
            onChange={(event) => {
              setStatus(event.target.value);
              if (page !== 1) setPage(1);
            }}
          >
            <option value="">All statuses</option>
            <option value="pending">Pending</option>
            <option value="approved">Approved</option>
            <option value="rejected">Rejected</option>
            <option value="cancelled">Cancelled</option>
          </select>

          <label className="filter-label" htmlFor="leave-start-date">
            From
          </label>
          <input
            id="leave-start-date"
            type="date"
            value={startDate}
            onChange={(event) => setStartDate(event.target.value)}
          />

          <label className="filter-label" htmlFor="leave-end-date">
            To
          </label>
          <input
            id="leave-end-date"
            type="date"
            value={endDate}
            onChange={(event) => setEndDate(event.target.value)}
          />

          <button className="btn-secondary" type="button" onClick={applyFilters}>
            Search
          </button>
          <button className="btn-secondary" type="button" onClick={clearFilters}>
            Clear Filters
          </button>
        </div>

        {loading ? (
          <Loading message="Loading leave requests..." />
        ) : loadError ? (
          <ErrorState
            message={loadError}
            onRetry={() => fetchLeaves()}
          />
        ) : leaves.length === 0 ? (
          <EmptyState
            message={
              hasActiveFilters
                ? "No leave requests match your search or filters."
                : "No leave requests have been submitted yet."
            }
          />
        ) : (
          <>
            <p className="results-line">
              Showing {leaves.length} of {total} leave requests
            </p>

            <div className="responsive-table">
              <div className="table-wrapper">
                <table>
                  <thead>
                    <tr>
                      <th>Employee</th>
                      <th>Employee #</th>
                      <th>Leave Type</th>
                      <th>Date Range</th>
                      <th>Reason</th>
                      <th>Status</th>
                      <th>Actions</th>
                    </tr>
                  </thead>

                  <tbody>
                    {leaves.map((leave) => (
                      <tr key={leave.id}>
                        <td data-label="Employee">
                          <span className="responsive-cell-value">
                            {leave.employee_name ||
                              `Employee #${leave.employee_id}`}
                          </span>
                        </td>

                        <td data-label="Employee #">
                          <span className="responsive-cell-value">
                            {leave.employee_number || "—"}
                          </span>
                        </td>

                        <td data-label="Leave Type">
                          <span className="responsive-cell-value">
                            {formatLeaveType(leave.leave_type)}
                          </span>
                        </td>

                        <td data-label="Date Range">
                          <span className="responsive-cell-value">
                            {formatDisplayDateRange(
                              leave.start_date,
                              leave.end_date
                            )}
                          </span>
                        </td>

                        <td data-label="Reason" className="text-cell">
                          <span className="responsive-cell-value">
                            {leave.reason || "—"}
                          </span>
                        </td>

                        <td data-label="Status">
                          <span className="responsive-cell-value">
                            <StatusBadge status={leave.status} />
                          </span>
                        </td>

                        <td data-label="Actions" className="action-cell">
                          {leave.status === "pending" ? (
                            <>
                              <button
                                className="btn-sm btn-primary"
                                disabled={actionPending !== null}
                                onClick={() =>
                                  handleAction(leave.id, "approve")
                                }
                              >
                                {isPending(leave.id, "approve")
                                  ? "Approving..."
                                  : "Approve"}
                              </button>

                              <button
                                className="btn-sm btn-danger"
                                disabled={actionPending !== null}
                                onClick={() =>
                                  handleAction(leave.id, "reject")
                                }
                              >
                                {isPending(leave.id, "reject")
                                  ? "Rejecting..."
                                  : "Reject"}
                              </button>
                            </>
                          ) : (
                            <span className="responsive-cell-value">
                              —
                            </span>
                          )}
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
            type="button"
            disabled={loading || page <= 1}
            onClick={() => setPage((current) => current - 1)}
          >
            Previous
          </button>

          <span className="results-line">
            {" "}
            Page {page} of {pages}{" "}
          </span>

          <button
            className="btn-secondary"
            type="button"
            disabled={loading || page >= pages}
            onClick={() => setPage((current) => current + 1)}
          >
            Next
          </button>
        </div>
      </main>
    </AppShell>
  );
}

export default AdminLeaves;