import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";

import { useAuth } from "./hooks/useAuth";
import Loading from "./components/Loading";
import ProtectedRoute from "./components/ProtectedRoute";
import AdminDashboard from "./pages/AdminDashboard";
import Dashboard from "./pages/Dashboard";
import Login from "./pages/Login";
import Leaves from "./pages/Leaves";
import Employees from "./pages/Employees";
import AdminLeaves from "./pages/AdminLeaves";
import AdminAttendance from "./pages/AdminAttendance";
import AuditLogs from "./pages/AuditLogs";
import NotFound from "./pages/NotFound";

function HomeRedirect() {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <main className="page-container">
        <Loading message="Checking your session..." />
      </main>
    );
  }

  if (user) {
    return (
      <Navigate
        to={user.role === "admin" ? "/admin" : "/dashboard"}
        replace
      />
    );
  }

  return <Navigate to="/login" replace />;
}

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route
          path="/"
          element={<HomeRedirect />}
        />

        <Route
          path="/login"
          element={<Login />}
        />

        {/* ADMIN ROUTES */}

        <Route
          path="/admin"
          element={
            <ProtectedRoute requiredRole="admin">
              <AdminDashboard />
            </ProtectedRoute>
          }
        />

        <Route
          path="/employees"
          element={
            <ProtectedRoute requiredRole="admin">
              <Employees />
            </ProtectedRoute>
          }
        />

        <Route
          path="/admin/attendance"
          element={
            <ProtectedRoute requiredRole="admin">
              <AdminAttendance />
            </ProtectedRoute>
          }
        />

        <Route
          path="/admin/leaves"
          element={
            <ProtectedRoute requiredRole="admin">
              <AdminLeaves />
            </ProtectedRoute>
          }
        />

        <Route
          path="/admin/audit-logs"
          element={
            <ProtectedRoute requiredRole="admin">
              <AuditLogs />
            </ProtectedRoute>
          }
        />

        {/* EMPLOYEE ROUTES */}

        <Route
          path="/dashboard"
          element={
            <ProtectedRoute requiredRole="employee">
              <Dashboard />
            </ProtectedRoute>
          }
        />

        <Route
          path="/leaves"
          element={
            <ProtectedRoute requiredRole={["admin", "employee"]}>
              <Leaves />
            </ProtectedRoute>
          }
        />

        {/* CATCH-ALL */}

        <Route
          path="*"
          element={<NotFound />}
        />
      </Routes>
    </BrowserRouter>
  );
}

export default App;