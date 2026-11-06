import { NavLink, Outlet , useNavigate} from "react-router-dom";
import {
  AudioLines,
  LayoutDashboard,
  Mic,
  ChartNoAxesCombined,
  History,
  Sparkles,
  LogOut,
} from "lucide-react";

import ChatbotWidget from "./ChatbotWidget";
import "./AppLayout.css";

const navItems = [
  { label: "Dashboard", path: "/dashboard", icon: LayoutDashboard },
  { label: "Analyze", path: "/upload", icon: AudioLines },
  { label: "Quick Practice", path: "/practice", icon: Mic },
  { label: "Progress", path: "/detailed-final", icon: ChartNoAxesCombined },
  // { label: "GenerateScript", path: "/GenerateScript", icon: Sparkles },
  { label: "PPT Analyzer", path:"/slide-prep",icon: Sparkles}
];

export default function AppLayout() {
  const navigate=useNavigate();
  return (
    <div className="app-shell">
      <header className="app-navbar">
        <NavLink to="/dashboard" className="app-brand">
          <span className="app-brand-icon">
            <AudioLines size={29} />
          </span>

          <span>
            <span className="app-brand-name">
              SpeakKaro<span>.AI</span>
            </span>
            <span className="app-brand-tagline">
              Speak. Analyse. Grow.
            </span>
          </span>
        </NavLink>

        <nav className="app-nav-links">
          {navItems.map(({ label, path, icon: Icon }) => (
            <NavLink
              key={label}
              to={path}
              className={({ isActive }) =>
                `app-nav-link ${isActive ? "active" : ""}`
              }
            >
              <Icon size={17} strokeWidth={1.8} />
              <span>{label}</span>
            </NavLink>
          ))}
        </nav>

        <div className="app-navbar-right">
          <span className="app-status-dot" />
          <span className="app-status-text">AI Coach</span>
          <span className="app-profile-icon"  style={{cursor:"pointer"}} onClick={()=>navigate("/")} >
            <LogOut size={18} />
            {/* L */}
          </span>
        </div>
      </header>

      <main className="app-main">
        <Outlet />
      </main>

      <ChatbotWidget />
    </div>
  );
}
