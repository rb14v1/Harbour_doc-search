import { NavLink, Outlet } from "react-router-dom";

import { useAuth } from "../auth/AuthContext";

export function AppLayout() {
  const { user, logout } = useAuth();

  return (
    <div className="app-shell">
      <header className="app-header">
        <div className="app-header-title">Doc Search</div>
        <nav className="app-nav">
          <NavLink to="/" end>Search</NavLink>
          <NavLink to="/documents">Documents</NavLink>
        </nav>
        <div className="app-header-user">
          <span>{user?.email}</span>
          <button onClick={logout}>Log out</button>
        </div>
      </header>
      <main className="app-content">
        <Outlet />
      </main>
    </div>
  );
}
