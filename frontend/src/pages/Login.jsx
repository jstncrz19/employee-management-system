import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";

import api from "../services/api";
import Loading from "../components/Loading";
import { getErrorMessage } from "../utils/errorMessage";

function Login() {
    const navigate = useNavigate();

    const { user, loading, login } = useAuth();

    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [error, setError] = useState("");
    const [submitting, setSubmitting] = useState(false);

    useEffect(() => {
        if (!loading && user) {
            navigate(
                user.role === "admin" ? "/admin" : "/dashboard",
                { replace: true }
            );
        }
    }, [user, loading, navigate]);

    if (loading) {
        return (
            <main className="page-container">
                <Loading message="Checking your session..." />
            </main>
        );
    }

    const handleSubmit = async (event) => {
        event.preventDefault();

        if (submitting) {
            return;
        }

        setError("");
        setSubmitting(true);

        try {
            const formData = new URLSearchParams();

            formData.append("username", email);
            formData.append("password", password);

            const response = await api.post("/auth/login", formData, {
                headers: {
                    "Content-Type": "application/x-www-form-urlencoded",
                },
            });

            localStorage.setItem("access_token", response.data.access_token);

            const userResponse = await api.get("/users/me");
            login(userResponse.data);

            if (userResponse.data.role === "admin") {
                navigate("/admin");
            } else {
                navigate("/dashboard");
            }

        } catch (error) {
            setError(
                getErrorMessage(error, "Login failed. Please try again.")
            );
        } finally {
            setSubmitting(false);
        }
    };

    return (
        <div className="login-page">
            <aside className="login-brand">
                <div className="login-brand-inner">
                    <div className="brand-lockup">
                        <span className="brand-mark">S</span>
                        <div>
                            <span className="brand-name">StaffPulse</span>
                            <span className="brand-sub">Employee Operations</span>
                        </div>
                    </div>

                    <div className="login-promo">
                        <h1>Workforce management in one clean view.</h1>
                        <p>
                            Track attendance, manage leave requests, and keep
                            your team&apos;s operations running smoothly.
                        </p>
                    </div>

                    <ul className="login-features">
                        <li>
                            <span className="material-symbols-outlined">
                                event_available
                            </span>
                            Daily attendance with check-in and check-out
                        </li>
                        <li>
                            <span className="material-symbols-outlined">
                                fact_check
                            </span>
                            Leave requests with balances and approvals
                        </li>
                        <li>
                            <span className="material-symbols-outlined">
                                insights
                            </span>
                            Live workforce overview for administrators
                        </li>
                    </ul>
                </div>
            </aside>

            <main className="login-panel">
                <div className="login-card">
                    <h2>Welcome back</h2>
                    <p className="login-subtitle">
                        Sign in with your work email to continue.
                    </p>

                    <form onSubmit={handleSubmit}>
                        <div>
                            <label htmlFor="login-email">Email</label>
                            <div className="input-with-icon">
                                <span className="material-symbols-outlined">
                                    mail
                                </span>
                                <input
                                    id="login-email"
                                    type="email"
                                    value={email}
                                    onChange={(event) => setEmail(event.target.value)}
                                    placeholder="you@company.com"
                                    required
                                />
                            </div>
                        </div>

                        <div>
                            <label htmlFor="login-password">Password</label>
                            <div className="input-with-icon">
                                <span className="material-symbols-outlined">
                                    lock
                                </span>
                                <input
                                    id="login-password"
                                    type="password"
                                    value={password}
                                    onChange={(event) => setPassword(event.target.value)}
                                    placeholder="Enter your password"
                                    required
                                />
                            </div>
                        </div>

                        {error && (
                            <div className="error form-alert">{error}</div>
                        )}

                        <button
                            className="btn-primary btn-block"
                            type="submit"
                            disabled={submitting}
                        >
                            {submitting ? "Signing in..." : "Sign in"}
                        </button>
                    </form>
                </div>
            </main>
        </div>
    );
}

export default Login;