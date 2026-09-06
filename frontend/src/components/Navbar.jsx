import { Link, useNavigate } from "react-router-dom";

import { useAuth } from "../hooks/useAuth";

function Navbar() {
  const navigate = useNavigate();
  const { user, logout } = useAuth();

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  if (!user) {
    return null;
  }

  const isAdmin = user.role === "admin";

  return (
    <nav>
      <h2>Employee Management System</h2>

      <div>
        {isAdmin ? (
          <>
            <Link to="/admin">Dashboard</Link>
            <Link to="/leaves">My Leaves</Link>
            <Link to="/employees">Employees</Link>
            <Link to="/admin/leaves">
              Leave Requests
            </Link>
            <Link to="/admin/attendance">
              Attendance
            </Link>
            <Link to="/admin/audit-logs">
              Audit Logs
            </Link>
          </>
        ) : (
          <>
            <Link to="/dashboard">Dashboard</Link>
            <Link to="/leaves">My Leaves</Link>
          </>
        )}

        <button className="btn-secondary" onClick={handleLogout}>
          Logout
        </button>
      </div>
    </nav>
  );
}

export default Navbar;
