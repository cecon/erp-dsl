import { Loader, Stack, Text } from '@mantine/core';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { useEffect, type ComponentType } from 'react';
import { useEngine } from './EngineProvider';

/* eslint-disable @typescript-eslint/no-explicit-any */

/**
 * Renders the dashboard page from a DSL schema.
 *
 * Fetches the 'dashboard' page schema and maps each component
 * to the corresponding widget via the widgetRegistry from EngineProvider.
 * No hardcoded data or switch/case — everything is schema + registry.
 */
export function DashboardRenderer() {
  const { apiClient, onPageContext, widgetRegistry = {} } = useEngine();
  const queryClient = useQueryClient();

  // Sync page context when navigating to dashboard
  useEffect(() => {
    onPageContext?.({
      pageKey: 'dashboard',
      pageTitle: 'Dashboard',
      entityEndpoint: null,
      pageSchema: null,
      viewMode: 'dashboard',
    });
  }, [onPageContext]);

  // Listen for schema refresh events (after publish/rollback)
  useEffect(() => {
    const handler = () => {
      queryClient.invalidateQueries({ queryKey: ['page', 'dashboard'] });
    };
    window.addEventListener('otto:refresh-page', handler);
    return () => window.removeEventListener('otto:refresh-page', handler);
  }, [queryClient]);

  const { data, isLoading, error } = useQuery({
    queryKey: ['page', 'dashboard'],
    queryFn: () => apiClient.get('/pages/dashboard').then((r) => r.data),
  });

  if (isLoading) {
    return (
      <Stack align="center" justify="center" h={400}>
        <Loader color="blue" size="lg" />
        <Text c="dimmed" size="sm">Loading dashboard…</Text>
      </Stack>
    );
  }

  if (error || !data) {
    return (
      <Stack align="center" justify="center" h={400}>
        <Text c="dimmed" size="sm">Dashboard schema not found.</Text>
      </Stack>
    );
  }

  const schema = data?.schema;
  const components = schema?.components ?? [];

  return (
    <Stack gap="xl">
      <div>
        <div className="page-header-title">{schema?.title || 'Dashboard'}</div>
        {schema?.description && (
          <div className="page-header-subtitle">{schema.description}</div>
        )}
      </div>

      {components.map((comp: any) => {
        const Component: ComponentType<any> | undefined = widgetRegistry[comp.type];
        if (!Component) {
          return (
            <Text key={comp.id} c="red" size="sm">
              Unknown dashboard component: {comp.type}
            </Text>
          );
        }
        return <Component key={comp.id} {...comp} />;
      })}
    </Stack>
  );
}
