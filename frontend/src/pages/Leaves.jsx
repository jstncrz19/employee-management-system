import { useEffect, useState } from "react";

import api from "../services/api";
import AppShell from "../components/layout/AppShell";
import Loading from "../components/Loading";
import EmptyState from "../components/EmptyState";
import ErrorState from "../components/ErrorState";
import PageHeader from "../components/PageHeader";
import LeaveBalances from "../components/LeaveBalances";
import LeaveCard from "../components/LeaveCard";
import { getErrorMessage } from "../utils/errorMessage";

function Leaves() {
  const [leaves, setLeaves] = useState([]);
  const [balances, setBalances] = useState([]);

  const [leaveType, setLeaveType] = useState("vacation");
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const [reason, setReason] = useState("");

  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [cancellingId, setCancellingId] = useState(null);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [reloadToken, setReloadToken] = useState(0);

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
      setLoading(true);
      setLoadError("");

      try {
        await fetchLeaves();
      } catch (error) {
        setLoadError(
          getErrorMessage(error, "Unable to load leave information.")
        );
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, [reloadToken]);

  const handleRetry = () => {
    setReloadToken((token) => token + 1);
  };

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
        getErrorMessage(error, "Unable to submit leave request.")
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
        getErrorMessage(error, "Unable to cancel leave request.")
      );
    } finally {
      setCancellingId(null);
    }
  };

  return (
    <AppShell>
      <main className="page-container">
        <PageHeader
          title="My Leaves"
          subtitle="View your leave balances and request time off."
        />

        {error && <div className="error">{error}</div>}
        {message && <div className="success">{message}</div>}

        {loading ? (
          <Loading message="Loading leave information..." />
        ) : loadError ? (
          <ErrorState
            message={loadError}
            onRetry={handleRetry}
          />
        ) : (
          <>
            <section>
              <h2>Leave Balances</h2>
              <LeaveBalances balances={balances} />
            </section>

            <div className="dashboard-two-col">
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

                  <div className="form-row">
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

                  <button
                    className="btn-primary"
                    type="submit"
                    disabled={submitting}
                  >
                    {submitting
                      ? "Submitting..."
                      : "Submit Leave Request"}
                  </button>
                </form>
              </section>

              <section>
                <h2>My Leave Requests</h2>

                {leaves.length > 0 ? (
                  <div className="record-stack">
                    {leaves.map((leave) => (
                      <LeaveCard leave={leave} key={leave.id}>
                        {(leave.status === "pending" ||
                          leave.status === "approved") && (
                          <button
                            className="btn-sm btn-danger"
                            onClick={() => handleCancel(leave.id)}
                            disabled={cancellingId !== null}
                          >
                            {cancellingId === leave.id
                              ? "Cancelling..."
                              : "Cancel"}
                          </button>
                        )}
                      </LeaveCard>
                    ))}
                  </div>
                ) : (
                  <EmptyState message="No leave requests found yet." />
                )}
              </section>
            </div>
          </>
        )}
      </main>
    </AppShell>
  );
}

export default Leaves;