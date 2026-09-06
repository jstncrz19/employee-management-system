import { Navigate } from "react-router-dom";

import { useAuth } from "../hooks/useAuth";
import Loading from "./Loading";

function ProtectedRoute({ children, requiredRole }) {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <main className="page-container">
        <Loading message="Checking your session..." />
      </main>
    );
  }

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  if (requiredRole) {
    const allowedRoles = Array.isArray(requiredRole)
      ? requiredRole
      : [requiredRole];

    if (!allowedRoles.includes(user.role)) {
      if (user.role === "admin") {
        return <Navigate to="/admin" replace />;
      }

      return <Navigate to="/dashboard" replace />;
    }
  }

  return children;
}

export default ProtectedRoute;
