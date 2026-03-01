import { FormEvent, useState } from "react";
import { useNavigate } from "react-router-dom";
import { API_BASE_URL } from "../config";
import { AuthSession } from "../types/auth";
import "./pages.css";

type AccountProps = {
  session: AuthSession;
  onAuth: (session: AuthSession) => void;
  onLogout: () => void;
};

const Account = ({ session, onAuth, onLogout }: AccountProps) => {
  const [newUsername, setNewUsername] = useState(session.username);
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [status, setStatus] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [updating, setUpdating] = useState(false);

  const [deletePassword, setDeletePassword] = useState("");
  const [deleteStatus, setDeleteStatus] = useState<string | null>(null);
  const [deleteError, setDeleteError] = useState<string | null>(null);
  const [deleting, setDeleting] = useState(false);

  const navigate = useNavigate();

  const handleUpdate = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setStatus(null);
    setError(null);

    const trimmedUsername = newUsername.trim();
    if (!currentPassword) {
      setError("Enter your current password to update the account.");
      return;
    }

    const usernameChanged =
      trimmedUsername.toLowerCase() !== session.username.toLowerCase();
    const passwordChanged = Boolean(newPassword);
    if (!usernameChanged && !passwordChanged) {
      setError("Change the username or password to update your account.");
      return;
    }

    setUpdating(true);
    try {
      const payload: Record<string, string> = {
        username: session.username,
        password: currentPassword,
      };

      if (usernameChanged) {
        payload.new_username = trimmedUsername;
      }
      if (passwordChanged) {
        payload.new_password = newPassword;
      }

      const response = await fetch(`${API_BASE_URL}/ml/auth/user`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        const detail = await response.text();
        throw new Error(detail || "Unable to update account.");
      }

      const updatedSession: AuthSession = await response.json();
      onAuth(updatedSession);
      setStatus("Account updated successfully.");
      setCurrentPassword("");
      setNewPassword("");
      setNewUsername(updatedSession.username);
    } catch (err) {
      const message =
        err instanceof Error ? err.message : "Unable to update account.";
      setError(message);
    } finally {
      setUpdating(false);
    }
  };

  const handleDelete = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setDeleteStatus(null);
    setDeleteError(null);

    if (!deletePassword) {
      setDeleteError("Enter your password to delete the account.");
      return;
    }

    setDeleting(true);
    try {
      const response = await fetch(`${API_BASE_URL}/ml/auth/user`, {
        method: "DELETE",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          username: session.username,
          password: deletePassword,
        }),
      });

      if (!response.ok) {
        const detail = await response.text();
        throw new Error(detail || "Unable to delete account.");
      }

      const payload: { message?: string } = await response.json();
      setDeleteStatus(payload.message ?? "Account deleted.");
      onLogout();
      navigate("/login", { replace: true });
    } catch (err) {
      const message =
        err instanceof Error ? err.message : "Unable to delete account.";
      setDeleteError(message);
    } finally {
      setDeleting(false);
    }
  };

  return (
    <section className="panel">
      <header className="panel__header">
        <h1>Account</h1>
        <p>Update your login details or delete your workspace account.</p>
      </header>

      <div className="settings-grid">
        <div className="settings-card">
          <h3>Update account</h3>
          <p>Change your username and/or password. Current password required.</p>
          <form onSubmit={handleUpdate}>
            <label>
              <span>New username</span>
              <input
                type="text"
                value={newUsername}
                onChange={(e) => setNewUsername(e.target.value)}
                autoComplete="username"
              />
            </label>
            <label>
              <span>New password</span>
              <input
                type="password"
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                autoComplete="new-password"
              />
            </label>
            <label>
              <span>Current password</span>
              <input
                type="password"
                value={currentPassword}
                onChange={(e) => setCurrentPassword(e.target.value)}
                autoComplete="current-password"
                required
              />
            </label>
            <button type="submit" className="primary" disabled={updating}>
              {updating ? "Saving..." : "Save changes"}
            </button>
          </form>
          {error && <div className="alert alert--error">{error}</div>}
          {status && <div className="alert alert--success">{status}</div>}
          <p className="muted">
            Tip: If you change your username, you will stay signed in with the
            new value automatically.
          </p>
        </div>

        <div className="settings-card">
          <h3>Delete account</h3>
          <p>Remove your account and stored credentials from this device.</p>
          <form onSubmit={handleDelete}>
            <label>
              <span>Confirm password</span>
              <input
                type="password"
                value={deletePassword}
                onChange={(e) => setDeletePassword(e.target.value)}
                autoComplete="current-password"
                required
              />
            </label>
            <button type="submit" className="danger" disabled={deleting}>
              {deleting ? "Deleting..." : "Delete account"}
            </button>
          </form>
          {deleteError && <div className="alert alert--error">{deleteError}</div>}
          {deleteStatus && (
            <div className="alert alert--success">{deleteStatus}</div>
          )}
          <p className="muted">
            This action clears your credentials and signs you out immediately.
          </p>
        </div>
      </div>
    </section>
  );
};

export default Account;
