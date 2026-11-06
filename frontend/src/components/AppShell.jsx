import { BookOpenCheck, ChartNoAxesCombined, Download, GraduationCap, LogOut, ShieldCheck, Trash2, Users } from "lucide-react";
import { useState } from "react";
import { NavLink, Outlet, useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { useAuth } from "../auth/useAuth";
import api, { errorMessage } from "../api/client";
import LanguageSwitcher from "./LanguageSwitcher";

const roleNavigation = {
  student: [{ path: "/student", label: "Learning", icon: BookOpenCheck }],
  teacher: [{ path: "/teacher", label: "Class overview", icon: ChartNoAxesCombined }],
  parent: [{ path: "/parent", label: "Child progress", icon: Users }],
  admin: [{ path: "/admin", label: "Administration", icon: ShieldCheck }],
};

export default function AppShell() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const { t } = useTranslation();
  const [privacyNotice, setPrivacyNotice] = useState("");
  const role = user?.role || "student";

  function signOut() {
    logout();
    navigate("/login");
  }

  async function exportData() {
    try {
      const { data } = await api.get("/auth/data-export");
      const url = URL.createObjectURL(new Blob([JSON.stringify(data, null, 2)], { type: "application/json" }));
      const link = document.createElement("a");
      link.href = url;
      link.download = "edubridge-personal-data.json";
      link.click();
      URL.revokeObjectURL(url);
      setPrivacyNotice("Your data export has started.");
    } catch (requestError) { setPrivacyNotice(errorMessage(requestError)); }
  }

  async function requestDeletion() {
    if (!window.confirm("Send a request to delete your account data for administrator review?")) return;
    try {
      await api.post("/auth/delete-request");
      setPrivacyNotice("Your request has been sent for administrator review.");
    } catch (requestError) { setPrivacyNotice(errorMessage(requestError)); }
  }

  return (
    <div className="app-frame">
      <aside className="side-rail">
        <NavLink className="brand-lockup" to={`/${role}`} aria-label="EduBridge home">
          <span className="brand-mark"><GraduationCap size={22} /></span>
          <span><strong>EduBridge</strong><small>LEARNING, IN CONTEXT</small></span>
        </NavLink>
        <div className="rail-caption">WORKSPACE</div>
        <nav className="rail-nav" aria-label="Main navigation">
          {(roleNavigation[role] || []).map(({ path, label, icon: Icon }) => (
            <NavLink key={path} to={path} className={({ isActive }) => `rail-link ${isActive ? "active" : ""}`}>
              <Icon size={18} /><span>{label}</span>
            </NavLink>
          ))}
        </nav>
        <div className="rail-bottom">
          <div className="privacy-mark"><span className="privacy-dot" /> Student data stays private</div>
          <button className="rail-link signout" type="button" onClick={signOut}><LogOut size={18} /><span>{t("signOut")}</span></button>
        </div>
      </aside>
      <main className="main-column">
        <header className="topbar">
          <div className="topbar-context"><span className="context-dot" /> EduBridge AI <span className="context-slash">/</span> {role}</div>
          <div className="topbar-actions">
            <div className="privacy-actions"><button className="icon-button" type="button" title="Export my data" aria-label="Export my data" onClick={exportData}><Download size={15} /></button><button className="icon-button" type="button" title="Request data deletion" aria-label="Request data deletion" onClick={requestDeletion}><Trash2 size={15} /></button></div>
            <LanguageSwitcher />
            <div className="user-chip"><span className="avatar">{user?.name?.slice(0, 1) || "E"}</span><span className="user-chip-name">{user?.name}</span></div>
          </div>
        </header>
        {privacyNotice && <div className="privacy-toast" role="status">{privacyNotice}<button type="button" className="icon-button" onClick={() => setPrivacyNotice("")} aria-label="Dismiss message">×</button></div>}
        <div className="page-content"><Outlet /></div>
      </main>
    </div>
  );
}