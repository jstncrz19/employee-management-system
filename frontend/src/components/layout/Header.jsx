import { useNavigate } from "react-router-dom";

import { useAuth } from "../../hooks/useAuth";

function Header({ onMenuToggle }) {
  const navigate = useNavigate();
  const { user, logout } = useAuth();

  const isAdmin = user?.role === "admin";
  const initial = user?.email?.charAt(0)?.toUpperCase() || "U";

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  return (
    <header className="app-header">
      <button
        className="icon-button menu-toggle"
        type="button"
        aria-label="Toggle navigation menu"
        onClick={onMenuToggle}
      >
        <span className="material-symbols-outlined">menu</span>
      </button>

      <div className="header-brand">
        <span className="brand-mark brand-mark-sm">S</span>
        <span className="header-brand-name">StaffPulse</span>
      </div>

      <div className="header-actions">
        <div className="user-menu">
          <span className="user-avatar">{initial}</span>
          <div className="user-menu-info">
            <span className="user-email">{user?.email}</span>
            <span className="user-role-text">
              {isAdmin ? "Administrator" : "Employee"}
            </span>
          </div>
          <button
            className="icon-button"
            type="button"
            aria-label="Logout"
            onClick={handleLogout}
          >
            <span className="material-symbols-outlined">logout</span>
          </button>
        </div>
      </div>
    </header>
  );
}

export default Header;