import { NavLink } from "react-router-dom";
import { ChangeEvent, useRef, useState } from "react";
import { AuthSession } from "../types/auth";

type NavItem = {
  label: string;
  path: string;
};

type SidebarProps = {
  items: NavItem[];
  session: AuthSession | null;
  onLogout?: () => void;
};

const Sidebar = ({ items, session, onLogout }: SidebarProps) => {
  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const [selectedFile, setSelectedFile] = useState<string | null>(null);

  const handleUploadClick = () => {
    fileInputRef.current?.click();
  };

  const handleFileChange = (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      setSelectedFile(file.name);
    } else {
      setSelectedFile(null);
    }
  };

  return (
    <aside className="sidebar">
      <div className="sidebar__brand">
        <span className="sidebar__title">Startup Success</span>
        <span className="sidebar__subtitle">Insights</span>
      </div>
      <nav className="sidebar__nav">
        {items.map((item) => (
          <NavLink
            key={item.path}
            to={item.path}
            className={({ isActive }) =>
              `sidebar__nav-item ${isActive ? "sidebar__nav-item--active" : ""}`
            }
            end={item.path === "/"}
          >
            {item.label}
          </NavLink>
        ))}
      </nav>
      <div className="sidebar__upload">
        <button type="button" className="upload-button" onClick={handleUploadClick}>
          Upload dataset
        </button>
        <input
          type="file"
          accept=".csv"
          ref={fileInputRef}
          className="upload-input"
          onChange={handleFileChange}
        />
        <span className="upload-hint">
          {selectedFile ? `Selected: ${selectedFile}` : "CSV files up to 5MB"}
        </span>
      </div>
      <div className="sidebar__session">
        {session ? (
          <>
            <div className="sidebar__user">
              <span className="sidebar__avatar">
                {session.username.slice(0, 1).toUpperCase()}
              </span>
              <div>
                <div className="sidebar__username">{session.username}</div>
                <div className="sidebar__status">Signed in</div>
              </div>
            </div>
            <button
              type="button"
              className="logout-button"
              onClick={() => onLogout?.()}
            >
              Sign out
            </button>
          </>
        ) : (
          <p className="sidebar__cta">Sign in to access predictions.</p>
        )}
      </div>
    </aside>
  );
};

export default Sidebar;
