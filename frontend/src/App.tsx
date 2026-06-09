import { NavLink, Navigate, Route, Routes } from "react-router-dom";

import { ChatPage } from "./pages/ChatPage";
import { MemoryPage } from "./pages/MemoryPage";
import { PatternPage } from "./pages/PatternPage";
import { TaskPage } from "./pages/TaskPage";

const navItems = [
  { to: "/chat", label: "Chat" },
  { to: "/memories", label: "Memory" },
  { to: "/patterns", label: "Pattern" },
  { to: "/tasks", label: "Task" }
];

export default function App() {
  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <span className="brand-mark">MG</span>
          <div>
            <h1>Growth Agent</h1>
            <p>Memory workbench</p>
          </div>
        </div>
        <nav className="nav-list" aria-label="Primary navigation">
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) => (isActive ? "nav-link active" : "nav-link")}
            >
              {item.label}
            </NavLink>
          ))}
        </nav>
      </aside>

      <main className="workspace">
        <Routes>
          <Route path="/" element={<Navigate to="/chat" replace />} />
          <Route path="/chat" element={<ChatPage />} />
          <Route path="/memories" element={<MemoryPage />} />
          <Route path="/patterns" element={<PatternPage />} />
          <Route path="/tasks" element={<TaskPage />} />
        </Routes>
      </main>
    </div>
  );
}
