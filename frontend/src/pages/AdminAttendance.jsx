import { useEffect, useState } from "react";

import api from "../services/api";
import Navbar from "../components/Navbar";

function AdminAttendance() {
  const [attendance, setAttendance] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const fetchAttendance = async () => {
    try {
      const response = await api.get("/attendance");

      setAttendance(response.data.items);
    } catch (error) {
      setError(
        error.response?.data?.detail ||
          "Unable to load attendance records."
      );
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAttendance();
  }, []);

  if (loading) {
    return <p>Loading attendance...</p>;
  }

  return (
    <div>
      <Navbar />

      <main className="page-container">
        <h1>Attendance</h1>

        {error && <div className="error">{error}</div>}

        {attendance.length === 0 ? (
          <p>No attendance records found.</p>
        ) : (
          <table>
            <thead>
              <tr>
                <th>Employee ID</th>
                <th>Date</th>
                <th>Time In</th>
                <th>Time Out</th>
                <th>Status</th>
              </tr>
            </thead>

            <tbody>
              {attendance.map((record) => (
                <tr key={record.id}>
                  <td>{record.employee_id}</td>
                  <td>{record.date}</td>
                  <td>{record.time_in || "—"}</td>
                  <td>{record.time_out || "—"}</td>
                  <td>{record.status}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </main>
    </div>
  );
}

export default AdminAttendance;