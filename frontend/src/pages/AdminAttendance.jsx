import { useCallback, useEffect, useState } from "react";

import api from "../services/api";
import Navbar from "../components/Navbar";

const LIMIT = 10;

function AdminAttendance() {
  const [attendance, setAttendance] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [searchInput, setSearchInput] = useState("");
  const [search, setSearch] = useState("");
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const [page, setPage] = useState(1);
  const [pages, setPages] = useState(0);
  const [total, setTotal] = useState(0);

  const fetchAttendance = useCallback(async (requestedPage = page) => {
    setLoading(true);
    setError("");
    try {
      const response = await api.get("/attendance", {
        params: {
          page: requestedPage,
          limit: LIMIT,
          ...(search && { search }),
          ...(startDate && { start_date: startDate }),
          ...(endDate && { end_date: endDate }),
        },
      });
      setAttendance(response.data.items);
      setPage(response.data.page);
      setPages(response.data.pages);
      setTotal(response.data.total);
    } catch (requestError) {
      setError(
        requestError.response?.data?.detail ||
          "Unable to load attendance records."
      );
    } finally {
      setLoading(false);
    }
  }, [endDate, page, search, startDate]);

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
    setStartDate("");
    setEndDate("");
    if (page !== 1) setPage(1);
  };

  return (
    <div>
      <Navbar />
      <main className="page-container">
        <h1>Attendance</h1>
        {error && <div className="error">{error}</div>}
        <div>
          <input
            type="search"
            placeholder="Search name, number, or email"
            value={searchInput}
            onChange={(event) => setSearchInput(event.target.value)}
            onKeyDown={(event) => {
              if (event.key === "Enter") applyFilters();
            }}
          />
          <label htmlFor="attendance-start-date">From</label>
          <input id="attendance-start-date" type="date" value={startDate}
            onChange={(event) => setStartDate(event.target.value)} />
          <label htmlFor="attendance-end-date">To</label>
          <input id="attendance-end-date" type="date" value={endDate}
            onChange={(event) => setEndDate(event.target.value)} />
          <button type="button" onClick={applyFilters}>Search</button>
          <button type="button" onClick={clearFilters}>Clear Filters</button>
        </div>

        {loading ? <p>Loading attendance...</p> : attendance.length === 0 ? (
          <p>No attendance records found.</p>
        ) : (
          <>
            <p>Showing {attendance.length} of {total} attendance records</p>
            <table>
              <thead><tr><th>Employee</th><th>Employee #</th><th>Date</th><th>Time In</th><th>Time Out</th><th>Status</th></tr></thead>
              <tbody>
                {attendance.map((record) => (
                  <tr key={record.id}>
                    <td>{record.employee_name || `Employee #${record.employee_id}`}</td>
                    <td>{record.employee_number || "—"}</td>
                    <td>{record.date}</td><td>{record.time_in || "—"}</td>
                    <td>{record.time_out || "—"}</td><td>{record.status}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </>
        )}
        <div>
          <button type="button" disabled={loading || page <= 1}
            onClick={() => setPage((current) => current - 1)}>Previous</button>
          <span> Page {page} of {pages} </span>
          <button type="button" disabled={loading || page >= pages}
            onClick={() => setPage((current) => current + 1)}>Next</button>
        </div>
      </main>
    </div>
  );
}

export default AdminAttendance;
