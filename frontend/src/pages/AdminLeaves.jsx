import { useEffect, useState } from "react";

import api from "../services/api";
import Navbar from "../components/Navbar";

function AdminLeaves() {
  const [leaves, setLeaves] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  const fetchLeaves = async () => {
    try {
      const response = await api.get("/leaves");

      setLeaves(response.data.items);
    } catch (error) {
      setError(
        error.response?.data?.detail ||
          "Unable to load leave requests."
      );
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchLeaves();
  }, []);

  const handleAction = async (leaveId, action) => {
    setError("");
    setMessage("");

    try {
      await api.patch(`/leaves/${leaveId}/${action}`);

      setMessage(
        action === "approve"
          ? "Leave request approved."
          : "Leave request rejected."
      );

      await fetchLeaves();
    } catch (error) {
      setError(
        error.response?.data?.detail ||
          "Unable to update leave request."
      );
    }
  };

  if (loading) {
    return <p>Loading leave requests...</p>;
  }

  return (
    <div>
      <Navbar />

      <main className="page-container">
        <h1>Leave Requests</h1>

        {error && <div className="error">{error}</div>}
        {message && <div className="success">{message}</div>}

        {leaves.length === 0 ? (
          <p>No leave requests found.</p>
        ) : (
          <table>
            <thead>
              <tr>
                <th>ID</th>
                <th>Employee</th>
                <th>Type</th>
                <th>Start Date</th>
                <th>End Date</th>
                <th>Reason</th>
                <th>Status</th>
                <th>Actions</th>
              </tr>
            </thead>

            <tbody>
              {leaves.map((leave) => (
                <tr key={leave.id}>
                  <td>{leave.id}</td>

                  <td>
                    Employee #{leave.employee_id}
                  </td>

                  <td>{leave.leave_type}</td>

                  <td>{leave.start_date}</td>

                  <td>{leave.end_date}</td>

                  <td>{leave.reason || "—"}</td>

                  <td>{leave.status}</td>

                  <td>
                    {leave.status === "pending" && (
                      <>
                        <button
                          onClick={() =>
                            handleAction(
                              leave.id,
                              "approve"
                            )
                          }
                        >
                          Approve
                        </button>

                        <button
                          onClick={() =>
                            handleAction(
                              leave.id,
                              "reject"
                            )
                          }
                        >
                          Reject
                        </button>
                      </>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </main>
    </div>
  );
}

export default AdminLeaves;