import { FormEvent, useState } from "react";

import { login, signUp } from "../api";

type AuthPageProps = {
  onAuth: (session: { token: string; username: string; email: string }) => void;
};

export function AuthPage({ onAuth }: AuthPageProps) {
  const [isSignUp, setIsSignUp] = useState(false);
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setLoading(true);
    setError("");

    try {
      const response = isSignUp
        ? await signUp({ username, email, password })
        : await login({ email, password });

      onAuth({
        token: response.access_token,
        username: response.username,
        email: response.email,
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Authentication failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="page auth-page">
      <section className="card auth-card">
        <h1>Happiness Dashboard</h1>
        <p>Sign in to continue or create a new account.</p>

        <form onSubmit={handleSubmit} className="form-grid">
          {isSignUp && (
            <label>
              Username
              <input
                required
                minLength={3}
                value={username}
                onChange={(event) => setUsername(event.target.value)}
                placeholder="your name"
              />
            </label>
          )}

          <label>
            Email
            <input
              required
              type="email"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              placeholder="you@example.com"
            />
          </label>

          <label>
            Password
            <input
              required
              type="password"
              minLength={6}
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              placeholder="minimum 6 characters"
            />
          </label>

          {error && <p className="error">{error}</p>}

          <button disabled={loading} type="submit">
            {loading ? "Please wait..." : isSignUp ? "Create account" : "Sign in"}
          </button>
        </form>

        <button className="text-button" onClick={() => setIsSignUp((value) => !value)}>
          {isSignUp ? "Already have an account? Sign in" : "No account yet? Sign up"}
        </button>
      </section>
    </main>
  );
}
