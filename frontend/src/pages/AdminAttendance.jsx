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
  formatDisplayDate,
  formatDisplayTime,
} from "../utils/formatters";

const LIMIT = 10;

function AdminAttendance() {
  const [attendance, setAttendance] = useState([]);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState("");
  const [searchInput, setSearchInput] = useState("");
  const [search, setSearch] = useState("");
  const [date, setDate] = useState("");
  const [page, setPage] = useState(1);
  const [pages, setPages] = useState(0);
  const [total, setTotal] = useState(0);

  const fetchAttendance = useCallback(async (requestedPage = page) => {
    setLoading(true);
    setLoadError("");
    try {
      const response = await api.get("/attendance", {
        params: {
          page: requestedPage,
          limit: LIMIT,
          ...(search && { search }),
          ...(date && { date }),
        },
      });
      setAttendance(response.data.items);
      setPage(response.data.page);
      setPages(response.data.pages);
      setTotal(response.data.total);
    } catch (requestError) {
      setLoadError(
        getErrorMessage(requestError, "Unable to load attendance records.")
      );
    } finally {
      setLoading(false);
    }
  }, [date, page, search]);

  useEffect(() => {
    const requestTimer = setTimeout(() => {
      fetchAttendance();
    }, 0);

    return () => clearTimeout(requestTimer);
  }, [fetchAttendance]);

  const applyFilters = () => {
    setSearch(searchInput.trim());
    if (page !== 1) setPage(1);
  };

  const clearFilters = () => {
    setSearchInput("");
    setSearch("");
    setDate("");
    if (page !== 1) setPage(1);
  };

  return (
    <AppShell>
      <main className="page-container">
        <PageHeader
          title="Attendance"
          subtitle="Monitor and search daily check-ins and check-outs."
        />

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

          <label className="filter-label" htmlFor="attendance-date">
            Date
          </label>
          <input
            id="attendance-date"
            type="date"
            value={date}
            onChange={(event) => setDate(event.target.value)}
          />

          <button className="btn-secondary" type="button" onClick={applyFilters}>
            Search
          </button>
          <button className="btn-secondary" type="button" onClick={clearFilters}>
            Clear Filters
          </button>
        </div>

        {loading ? (
          <Loading message="Loading attendance records..." />
        ) : loadError ? (
          <ErrorState
            message={loadError}
            onRetry={() => fetchAttendance()}
          />
        ) : attendance.length === 0 ? (
          <EmptyState
            message={
              search || date
                ? "No attendance records match your search or filters."
                : "No attendance records found for the selected date."
            }
          />
        ) : (
          <>
            <p className="results-line">
              Showing {attendance.length} of {total} attendance records
            </p>

            <div className="responsive-table">
              <div className="table-wrapper">
                <table>
                  <thead>
                    <tr>
                      <th>Employee</th>
                      <th>Employee #</th>
                      <th>Date</th>
                      <th>Time In</th>
                      <th>Time Out</th>
                      <th>Status</th>
                    </tr>
                  </thead>

                  <tbody>
                    {attendance.map((record) => (
                      <tr key={record.id}>
                        <td data-label="Employee">
                          <span className="responsive-cell-value">
                            {record.employee_name ||
                              `Employee #${record.employee_id}`}
                          </span>
                        </td>

                        <td data-label="Employee #">
                          <span className="responsive-cell-value">
                            {record.employee_number || "—"}
                          </span>
                        </td>

                        <td data-label="Date">
                          <span className="responsive-cell-value">
                            {formatDisplayDate(record.date)}
                          </span>
                        </td>

                        <td data-label="Time In">
                          <span className="responsive-cell-value">
                            {record.time_in
                              ? formatDisplayTime(record.time_in)
                              : "—"}
                          </span>
                        </td>

                        <td data-label="Time Out">
                          <span className="responsive-cell-value">
                            {record.time_out
                              ? formatDisplayTime(record.time_out)
                              : "—"}
                          </span>
                        </td>

                        <td data-label="Status">
                          <span className="responsive-cell-value">
                            <StatusBadge status={record.status} />
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

export default AdminAttendance;