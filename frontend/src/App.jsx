import { lazy, Suspense } from "react";
import { Navigate, Route, Routes } from "react-router-dom";
import { useAuth } from "./auth/useAuth";
import AppShell from "./components/AppShell";
import Login from "./pages/Login";

const StudentDashboard = lazy(() => import("./pages/student/StudentDashboard"));
const TeacherDashboard = lazy(() => import("./pages/teacher/TeacherDashboard"));
const ParentDashboard = lazy(() => import("./pages/parent/ParentDashboard"));
const AdminDashboard = lazy(() => import("./pages/admin/AdminDashboard"));

function ProtectedRoute({ role, children }) {
  const { user } = useAuth();
  if (!user) return <Navigate to="/login" replace />;
  if (user.role !== role) return <Navigate to={`/${user.role}`} replace />;
  return children || <AppShell />;
}

function HomeRedirect() {
  const { user } = useAuth();
  return <Navigate to={user ? `/${user.role}` : "/login"} replace />;
}

export default function App() {
  return (
    <Suspense fallback={<div className="loading-state">Loading your workspace...</div>}>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route element={<ProtectedRoute role="student" />}><Route path="/student" element={<StudentDashboard />} /></Route>
        <Route element={<ProtectedRoute role="teacher" />}><Route path="/teacher" element={<TeacherDashboard />} /></Route>
        <Route element={<ProtectedRoute role="parent" />}><Route path="/parent" element={<ParentDashboard />} /></Route>
        <Route element={<ProtectedRoute role="admin" />}><Route path="/admin" element={<AdminDashboard />} /></Route>
        <Route path="/" element={<HomeRedirect />} />
        <Route path="*" element={<HomeRedirect />} />
      </Routes>
    </Suspense>
  );
}