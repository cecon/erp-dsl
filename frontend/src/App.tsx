import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom';
import { EngineProvider, PageRenderer, DashboardRenderer } from '@erp-dsl/engine';
import type { PageContext } from '@erp-dsl/engine';
import { StatsGrid } from '@erp-dsl/widgets';
import { ActivityFeed } from '@erp-dsl/widgets';
import { QuickActions } from '@erp-dsl/widgets';
import { CoreLayout } from './core/layout/CoreLayout';
import { Login } from './pages/Login';
import { SettingsPage } from './pages/SettingsPage';
import { ComponentShowcase } from './pages/ComponentShowcase';
import { useAuthStore } from './state/authStore';
import { OttoProvider, useOttoContext } from './features/otto';
import { componentRegistry } from './core/engine/ComponentRegistry';
import api from './services/api';
import { useCallback } from 'react';

/**
 * Widget registry for dashboard components.
 * Maps DSL type strings to widget components from @erp-dsl/widgets.
 */
const widgetRegistry = {
  stats_grid: StatsGrid,
  activity_feed: ActivityFeed,
  quick_actions: QuickActions,
};

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const token = useAuthStore((s) => s.token);
  if (!token) return <Navigate to="/login" replace />;
  return <>{children}</>;
}

/**
 * Inner app wrapped with EngineProvider to inject
 * project-specific apiClient, registries, and page context callback.
 */
function AppLayout() {
  const { setContext: setOttoContext } = useOttoContext();

  const handlePageContext = useCallback((ctx: PageContext) => {
    setOttoContext(ctx as Parameters<typeof setOttoContext>[0]);
  }, [setOttoContext]);

  return (
    <EngineProvider
      apiClient={api}
      onPageContext={handlePageContext}
      componentRegistry={componentRegistry}
      widgetRegistry={widgetRegistry}
    >
      <CoreLayout>
        <Routes>
          <Route path="/" element={<DashboardRenderer />} />
          <Route path="/components" element={<ComponentShowcase />} />
          <Route path="/pages/:pageKey" element={<PageRenderer />} />
          <Route path="/settings" element={<SettingsPage />} />
        </Routes>
      </CoreLayout>
    </EngineProvider>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <OttoProvider>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route
            path="/*"
            element={
              <ProtectedRoute>
                <AppLayout />
              </ProtectedRoute>
            }
          />
        </Routes>
      </OttoProvider>
    </BrowserRouter>
  );
}
