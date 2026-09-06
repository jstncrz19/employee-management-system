import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";

import api from "../services/api";

function Login() {
    const navigate = useNavigate();

    const { user, loading, login } = useAuth();

    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [error, setError] = useState("");

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
                <p>Checking your session...</p>
            </main>
        );
    }

    const handleSubmit = async (event) => {
        event.preventDefault();
        setError("");

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
                error.response?.data?.detail || "Login failed. Please try again."
            );
        }
    };

    return (
        <div>
            <main className="page-container">
                <h1>Employee Management System</h1>

                <h2>Login</h2>

                <form onSubmit={handleSubmit}>
                    <div>
                        <label>Email</label>
                        <input
                            type="email"
                            value={email}
                            onChange={(event) => setEmail(event.target.value)}
                            required
                        />
                    </div>

                    <div>
                        <label>Password</label>
                        <input
                            type="password"
                            value={password}
                            onChange={(event) => setPassword(event.target.value)}
                            required
                        />
                    </div>

                    {error && <div className="error">{error}</div>}

                    <button type="submit">Login</button>
                </form>
            </main>
        </div>
    );
}

export default Login;
