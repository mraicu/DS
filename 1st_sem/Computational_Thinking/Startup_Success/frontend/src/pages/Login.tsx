import { FormEvent, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { API_BASE_URL } from "../config";
import { AuthSession } from "../types/auth";
import "./pages.css";

type LoginProps = {
    onAuth: (session: AuthSession) => void;
    session: AuthSession | null;
};

const Login = ({ onAuth, session }: LoginProps) => {
    const [mode, setMode] = useState<"login" | "register">("login");
    const [username, setUsername] = useState("");
    const [password, setPassword] = useState("");
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const navigate = useNavigate();

    useEffect(() => {
        if (session) {
            navigate("/");
        }
    }, [session, navigate]);

    const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
        event.preventDefault();
        setLoading(true);
        setError(null);

        try {
            const trimmedUsername = username.trim();
            if (!trimmedUsername || !password) {
                setError("Username and password are required.");
                setLoading(false);
                return;
            }

            const endpoint = mode === "login" ? "login" : "register";
            const response = await fetch(
                `${API_BASE_URL}/ml/auth/${endpoint}`,
                {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                        username: trimmedUsername,
                        password,
                    }),
                }
            );

            if (!response.ok) {
                const detail = await response.text();
                throw new Error(detail || "Unable to authenticate.");
            }

            const payload: AuthSession = await response.json();
            onAuth(payload);
            navigate("/");
        } catch (err) {
            const message =
                err instanceof Error ? err.message : "Authentication failed.";
            setError(message);
        } finally {
            setLoading(false);
        }
    };

    return (
        <section className="panel auth-panel">
            <header className="panel__header">
                <h1>
                    {mode === "login" ? "Welcome back" : "Create an account"}
                </h1>
            </header>

            <div className="auth-toggle">
                <button
                    type="button"
                    className={mode === "login" ? "active" : ""}
                    onClick={() => setMode("login")}
                    disabled={loading}
                >
                    Login
                </button>
                <button
                    type="button"
                    className={mode === "register" ? "active" : ""}
                    onClick={() => setMode("register")}
                    disabled={loading}
                >
                    Sign up
                </button>
            </div>

            <form className="auth-form" onSubmit={handleSubmit}>
                <label>
                    <span>Username</span>
                    <input
                        type="text"
                        name="username"
                        value={username}
                        onChange={(e) => setUsername(e.target.value)}
                        autoComplete="username"
                        required
                    />
                </label>
                <label>
                    <span>Password</span>
                    <input
                        type="password"
                        name="password"
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                        autoComplete={
                            mode === "login"
                                ? "current-password"
                                : "new-password"
                        }
                        required
                    />
                </label>
                <button type="submit" disabled={loading}>
                    {loading
                        ? "Please wait..."
                        : mode === "login"
                        ? "Login"
                        : "Create account"}
                </button>
            </form>

            {error && <div className="alert alert--error">{error}</div>}
            <p className="auth-hint">
                Passwords are hashed and stored in a local text file on the
                backend server.
            </p>
        </section>
    );
};

export default Login;
