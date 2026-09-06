import { Link } from "react-router-dom";

import { useAuth } from "../hooks/useAuth";
import Loading from "../components/Loading";

function NotFound() {
  const { user, loading } = useAuth();

  const homePath = user?.role === "admin" ? "/admin" : "/dashboard";
  const homeLabel = user?.role === "admin"
    ? "Go to Admin Dashboard"
    : "Go to Dashboard";

  return (
    <main className="page-container">
      <h1>Page Not Found</h1>

      <section>
        <p>
          The page you are looking for does not exist or has been moved.
        </p>

        {loading ? (
          <Loading message="Checking your session..." />
        ) : (
          <Link
            className="link-button"
            to={user ? homePath : "/login"}
          >
            {user ? homeLabel : "Go to Login"}
          </Link>
        )}
      </section>
    </main>
  );
}

export default NotFound;