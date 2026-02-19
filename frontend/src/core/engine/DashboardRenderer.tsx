import { type ComponentType } from 'react';
import { Loader, Stack, Text } from '@mantine/core';
import { useQuery } from '@tanstack/react-query';
import api from '../../services/api';
import { StatsGrid } from '../../components/dashboard/StatCard';
import { ActivityFeed } from '../../components/dashboard/ActivityFeed';
import { QuickActions } from '../../components/dashboard/QuickActions';

/* eslint-disable @typescript-eslint/no-explicit-any */

/**
 * Dashboard widget registry.
 *
 * Maps DSL component type strings to widget components.
 * To add a new widget type, register it here.
 */
const dashboardRegistry: Record<string, ComponentType<any>> = {
  stats_grid: StatsGrid,
  activity_feed: ActivityFeed,
  quick_actions: QuickActions,
};

/**
 * Renders the dashboard page from a DSL schema.
 *
 * Fetches the 'dashboard' page schema and maps each component
 * to the corresponding widget via the dashboardRegistry.
 * No hardcoded data or switch/case — everything is schema + registry.
 */
export function DashboardRenderer() {
  const { data, isLoading, error } = useQuery({
    queryKey: ['page', 'dashboard'],
    queryFn: () => api.get('/pages/dashboard').then((r) => r.data),
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
        const Component = dashboardRegistry[comp.type];
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
