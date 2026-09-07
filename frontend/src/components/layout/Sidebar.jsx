import { NavLink, useNavigate } from "react-router-dom";

import { useAuth } from "../../hooks/useAuth";

const ADMIN_LINKS = [
  { to: "/admin", label: "Dashboard", icon: "dashboard" },
  { to: "/employees", label: "Employees", icon: "group" },
  { to: "/admin/attendance", label: "Attendance", icon: "event_available" },
  { to: "/admin/leaves", label: "Leave Management", icon: "fact_check" },
  { to: "/admin/audit-logs", label: "Audit Logs", icon: "receipt_long" },
  { to: "/leaves", label: "My Leaves", icon: "holiday_village" },
];

const EMPLOYEE_LINKS = [
  { to: "/dashboard", label: "Dashboard", icon: "dashboard" },
  { to: "/leaves", label: "My Leaves", icon: "holiday_village" },
];

function Sidebar({ open, onClose }) {
  const navigate = useNavigate();
  const { user, logout } = useAuth();

  const isAdmin = user?.role === "admin";
  const links = isAdmin ? ADMIN_LINKS : EMPLOYEE_LINKS;
  const initial = user?.email?.charAt(0)?.toUpperCase() || "U";
  const roleLabel = isAdmin ? "Administrator" : "Employee";

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  return (
    <aside className={`app-sidebar ${open ? "is-open" : ""}`}>
      <button
        className="sidebar-backdrop"
        type="button"
        aria-label="Close navigation"
        onClick={onClose}
      />

      <div className="sidebar-panel">
        <div className="sidebar-brand">
          <span className="brand-mark">S</span>
          <div>
            <span className="brand-name">StaffPulse</span>
            <span className="brand-sub">Employee Operations</span>
          </div>
        </div>

        <nav className="sidebar-nav">
          {links.map((link) => (
            <NavLink
              key={link.to}
              to={link.to}
              end={link.to === "/admin" || link.to === "/dashboard"}
              className={({ isActive }) =>
                `sidebar-link ${isActive ? "is-active" : ""}`
              }
              onClick={onClose}
            >
              <span className="material-symbols-outlined">{link.icon}</span>
              <span>{link.label}</span>
            </NavLink>
          ))}
        </nav>

        <div className="sidebar-footer">
          <div className="sidebar-user">
            <span className="user-avatar">{initial}</span>
            <div className="user-meta">
              <span className="user-email">{user?.email}</span>
              <span className="user-role-text">{roleLabel}</span>
            </div>
          </div>

          <button
            className="sidebar-logout"
            type="button"
            onClick={handleLogout}
          >
            <span className="material-symbols-outlined">logout</span>
            <span>Logout</span>
          </button>
        </div>
      </div>
    </aside>
  );
}

export default Sidebar;