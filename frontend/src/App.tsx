import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom';
import { CoreLayout } from './core/layout/CoreLayout';
import { PageRenderer } from './core/engine/PageRenderer';
import { DashboardRenderer } from './core/engine/DashboardRenderer';
import { Login } from './pages/Login';
import { useAuthStore } from './state/authStore';

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const token = useAuthStore((s) => s.token);
  if (!token) return <Navigate to="/login" replace />;
  return <>{children}</>;
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route
          path="/*"
          element={
            <ProtectedRoute>
              <CoreLayout>
                <Routes>
                  <Route path="/" element={<DashboardRenderer />} />
                  <Route path="/pages/:pageKey" element={<PageRenderer />} />
                </Routes>
              </CoreLayout>
            </ProtectedRoute>
          }
        />
      </Routes>
    </BrowserRouter>
  );
}
