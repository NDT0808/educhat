import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { AuthProvider } from "./context/AuthContext";
import ProtectedRoute from "./components/ProtectedRoute";
import RoleGuard from "./components/RoleGuard";
import AppShell from "./components/Layout/AppShell";
import LoginPage from "./pages/LoginPage";
import UserHomePage from "./pages/UserHomePage";
import AdminDashboardPage from "./pages/AdminDashboardPage";
import PlannerPage from "./pages/PlannerPage";
import CalendarPage from "./pages/CalendarPage";
import FeedbackPage from "./pages/FeedbackPage";
import InsightsPage from "./pages/InsightsPage";
import CurriculumPage from "./pages/CurriculumPage";
import TimetablePage from "./pages/TimetablePage";
import OCRPage from "./pages/OCRPage";

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          {/* Public Routes */}
          <Route path="/login" element={<LoginPage />} />

          {/* Protected Routes with Layout */}
          <Route
            path="/"
            element={
              <ProtectedRoute>
                <AppShell />
              </ProtectedRoute>
            }
          >
            <Route index element={<UserHomePage />} />
            <Route path="planner" element={<PlannerPage />} />
            <Route path="calendar" element={<CalendarPage />} />
            <Route path="feedback" element={<FeedbackPage />} />
            <Route path="insights" element={<InsightsPage />} />
            <Route path="curriculum" element={<CurriculumPage />} />
            <Route path="timetable" element={<TimetablePage />} />
            <Route path="ocr" element={<OCRPage />} />

            {/* Admin Only Routes */}
            <Route
              path="admin"
              element={
                <RoleGuard allowedRoles={["ADMIN"]}>
                  <AdminDashboardPage />
                </RoleGuard>
              }
            />

            {/* Placeholder for other routes */}
            <Route path="knowledge" element={<div className="flex items-center justify-center h-full text-slate-400 font-medium">Knowledge Search feature coming soon...</div>} />
            <Route path="settings" element={<div className="flex items-center justify-center h-full text-slate-400 font-medium">Settings feature coming soon...</div>} />
          </Route>

          {/* Fallback */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}
