import { useEffect, useState } from "react";

import api from "../services/api";
import Navbar from "../components/Navbar";

function Leaves() {
  const [leaves, setLeaves] = useState([]);
  const [balances, setBalances] = useState([]);

  const [leaveType, setLeaveType] = useState("vacation");
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const [reason, setReason] = useState("");

  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [cancellingId, setCancellingId] = useState(null);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  const fetchLeaves = async () => {
    const [leavesResponse, balancesResponse] = await Promise.all([
      api.get("/leaves/me"),
      api.get("/leaves/balance/me"),
    ]);

    setLeaves(leavesResponse.data);
    setBalances(balancesResponse.data);
  };

  useEffect(() => {
    const loadData = async () => {
      try {
        await fetchLeaves();
      } catch (error) {
        setError(
          error.response?.data?.detail ||
            "Unable to load leave information."
        );
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, []);

  const handleSubmit = async (event) => {
    event.preventDefault();

    setError("");
    setMessage("");
    setSubmitting(true);

    try {
      await api.post("/leaves", {
        leave_type: leaveType,
        start_date: startDate,
        end_date: endDate,
        reason: reason || null,
      });

      setMessage("Leave request submitted successfully.");

      setStartDate("");
      setEndDate("");
      setReason("");

      await fetchLeaves();
    } catch (error) {
      setError(
        error.response?.data?.detail ||
          "Unable to submit leave request."
      );
    } finally {
      setSubmitting(false);
    }
  };

  const handleCancel = async (leaveId) => {
    setError("");
    setMessage("");
    setCancellingId(leaveId);

    try {
      await api.patch(`/leaves/${leaveId}/cancel`);

      setMessage("Leave request cancelled successfully.");

      await fetchLeaves();
    } catch (error) {
      setError(
        error.response?.data?.detail ||
          "Unable to cancel leave request."
      );
    } finally {
      setCancellingId(null);
    }
  };

  if (loading) {
    return <p>Loading leave information...</p>;
  }

  return (
    <div>
      <Navbar />

      <main className="page-container">
        <h1>Leave Management</h1>

        {error && <div className="error">{error}</div>}
        {message && <div className="success">{message}</div>}

        <section>
          <h2>Leave Balances</h2>

          {balances.length > 0 ? (
            <ul>
              {balances.map((balance) => (
                <li key={balance.leave_type}>
                  <strong>{balance.leave_type}</strong>
                  {" — "}
                  Total: {balance.total_days}
                  {" | "}
                  Used: {balance.used_days}
                  {" | "}
                  Remaining: {balance.remaining_days}
                </li>
              ))}
            </ul>
          ) : (
            <p>No leave balances available.</p>
          )}
        </section>

        <section>
          <h2>Request Leave</h2>

          <form onSubmit={handleSubmit}>
            <div>
              <label htmlFor="leave-type">
                Leave Type
              </label>

              <select
                id="leave-type"
                value={leaveType}
                onChange={(event) =>
                  setLeaveType(event.target.value)
                }
              >
                <option value="vacation">Vacation</option>
                <option value="sick">Sick</option>
                <option value="emergency">Emergency</option>
              </select>
            </div>

            <div>
              <label htmlFor="start-date">
                Start Date
              </label>

              <input
                id="start-date"
                type="date"
                value={startDate}
                onChange={(event) =>
                  setStartDate(event.target.value)
                }
                required
              />
            </div>

            <div>
              <label htmlFor="end-date">
                End Date
              </label>

              <input
                id="end-date"
                type="date"
                value={endDate}
                onChange={(event) =>
                  setEndDate(event.target.value)
                }
                required
              />
            </div>

            <div>
              <label htmlFor="reason">
                Reason
              </label>

              <textarea
                id="reason"
                value={reason}
                onChange={(event) =>
                  setReason(event.target.value)
                }
                maxLength={1000}
              />
            </div>

            <button type="submit" disabled={submitting}>
              {submitting
                ? "Submitting..."
                : "Submit Leave Request"}
            </button>
          </form>
        </section>

        <section>
          <h2>My Leave Requests</h2>

          {leaves.length > 0 ? (
            <ul>
              {leaves.map((leave) => (
                <li key={leave.id}>
                  <div>
                    <strong>{leave.leave_type}</strong>
                  </div>

                  <div>
                    {leave.start_date} → {leave.end_date}
                  </div>

                  <div>
                    Status: {leave.status}
                  </div>

                  {leave.reason && (
                    <div>
                      Reason: {leave.reason}
                    </div>
                  )}

                  {(leave.status === "pending" ||
                    leave.status === "approved") && (
                    <button
                      onClick={() => handleCancel(leave.id)}
                      disabled={cancellingId !== null}
                    >
                      {cancellingId === leave.id
                        ? "Cancelling..."
                        : "Cancel"}
                    </button>
                  )}
                </li>
              ))}
            </ul>
          ) : (
            <p>No leave requests found.</p>
          )}
        </section>
      </main>
    </div>
  );
}

export default Leaves;