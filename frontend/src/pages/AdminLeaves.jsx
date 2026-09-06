import { useCallback, useEffect, useState } from "react";

import api from "../services/api";
import Navbar from "../components/Navbar";

const LIMIT = 10;

function AdminLeaves() {
  const [leaves, setLeaves] = useState([]);
  const [loading, setLoading] = useState(true);
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

  const fetchLeaves = useCallback(async (requestedPage = page) => {
    setLoading(true);
    setError("");
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
      setError(
        requestError.response?.data?.detail ||
          "Unable to load leave requests."
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
    setError("");
    setMessage("");
    try {
      await api.patch(`/leaves/${leaveId}/${action}`);
      setMessage(
        action === "approve" ? "Leave request approved." : "Leave request rejected."
      );
      await fetchLeaves();
    } catch (requestError) {
      setError(
        requestError.response?.data?.detail ||
          "Unable to update leave request."
      );
    }
  };

  return (
    <div>
      <Navbar />
      <main className="page-container">
        <h1>Leave Requests</h1>
        {error && <div className="error">{error}</div>}
        {message && <div className="success">{message}</div>}
        <div>
          <input type="search" placeholder="Search name, number, or email"
            value={searchInput} onChange={(event) => setSearchInput(event.target.value)}
            onKeyDown={(event) => { if (event.key === "Enter") applyFilters(); }} />
          <select value={status} onChange={(event) => { setStatus(event.target.value); if (page !== 1) setPage(1); }}>
            <option value="">All statuses</option>
            <option value="pending">Pending</option>
            <option value="approved">Approved</option>
            <option value="rejected">Rejected</option>
            <option value="cancelled">Cancelled</option>
          </select>
          <label htmlFor="leave-start-date">From</label>
          <input id="leave-start-date" type="date" value={startDate}
            onChange={(event) => setStartDate(event.target.value)} />
          <label htmlFor="leave-end-date">To</label>
          <input id="leave-end-date" type="date" value={endDate}
            onChange={(event) => setEndDate(event.target.value)} />
          <button type="button" onClick={applyFilters}>Search</button>
          <button type="button" onClick={clearFilters}>Clear Filters</button>
        </div>

        {loading ? <p>Loading leave requests...</p> : leaves.length === 0 ? (
          <p>No leave requests found.</p>
        ) : (
          <>
            <p>Showing {leaves.length} of {total} leave requests</p>
            <table>
              <thead><tr><th>Employee</th><th>Employee #</th><th>Type</th><th>Start</th><th>End</th><th>Reason</th><th>Status</th><th>Actions</th></tr></thead>
              <tbody>{leaves.map((leave) => (
                <tr key={leave.id}>
                  <td>{leave.employee_name || `Employee #${leave.employee_id}`}</td>
                  <td>{leave.employee_number || "—"}</td><td>{leave.leave_type}</td>
                  <td>{leave.start_date}</td><td>{leave.end_date}</td>
                  <td>{leave.reason || "—"}</td><td>{leave.status}</td>
                  <td>{leave.status === "pending" && <><button onClick={() => handleAction(leave.id, "approve")}>Approve</button><button onClick={() => handleAction(leave.id, "reject")}>Reject</button></>}</td>
                </tr>
              ))}</tbody>
            </table>
          </>
        )}
        <div>
          <button type="button" disabled={loading || page <= 1} onClick={() => setPage((current) => current - 1)}>Previous</button>
          <span> Page {page} of {pages} </span>
          <button type="button" disabled={loading || page >= pages} onClick={() => setPage((current) => current + 1)}>Next</button>
        </div>
      </main>
    </div>
  );
}

export default AdminLeaves;
