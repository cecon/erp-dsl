import { createContext, useContext, type ComponentType, type ReactNode } from 'react';

/* eslint-disable @typescript-eslint/no-explicit-any */

/**
 * Shape of the API client that consuming apps must provide.
 * Matches the Axios instance API surface used by the engine.
 */
export interface EngineApiClient {
  get: (url: string, config?: any) => Promise<{ data: any }>;
  post: (url: string, data?: any) => Promise<{ data: any }>;
  put: (url: string, data?: any) => Promise<{ data: any }>;
  delete: (url: string) => Promise<{ data: any }>;
}

/**
 * Page context information emitted by PageRenderer/DashboardRenderer.
 * Consumers can use this for AI assistants, breadcrumbs, etc.
 */
export interface PageContext {
  pageKey: string | null;
  pageTitle: string | null;
  entityEndpoint: string | null;
  pageSchema: any | null;
  viewMode: string | null;
}

export interface EngineConfig {
  /** HTTP client for data fetching and mutations */
  apiClient: EngineApiClient;
  /** Optional callback invoked when page context changes */
  onPageContext?: (ctx: PageContext) => void;
  /** Registry mapping DSL type strings to field/component implementations */
  componentRegistry: Record<string, ComponentType<any>>;
  /** Registry mapping DSL widget type strings to dashboard widget components */
  widgetRegistry?: Record<string, ComponentType<any>>;
}

const EngineContext = createContext<EngineConfig | null>(null);

/**
 * Provides engine configuration to all engine components.
 *
 * Wrap your app (or a subtree) with this provider and pass in
 * your project-specific apiClient, registries, and callbacks.
 */
export function EngineProvider({
  children,
  ...config
}: EngineConfig & { children: ReactNode }) {
  return (
    <EngineContext.Provider value={config}>
      {children}
    </EngineContext.Provider>
  );
}

/**
 * Hook to access the engine configuration.
 * Must be used within an EngineProvider.
 */
export function useEngine(): EngineConfig {
  const ctx = useContext(EngineContext);
  if (!ctx) {
    throw new Error('useEngine must be used within an <EngineProvider>');
  }
  return ctx;
}
