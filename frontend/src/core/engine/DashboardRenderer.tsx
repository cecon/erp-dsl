import { Loader, Stack, Text } from '@mantine/core';
import { useQuery } from '@tanstack/react-query';
import api from '../../services/api';
import { StatsGrid } from '../../components/dashboard/StatCard';
import { ActivityFeed } from '../../components/dashboard/ActivityFeed';
import { QuickActions } from '../../components/dashboard/QuickActions';

/* eslint-disable @typescript-eslint/no-explicit-any */

/**
 * Renders the dashboard page from a DSL schema.
 *
 * Fetches the 'dashboard' page schema and maps each component
 * to the corresponding dashboard widget. No hardcoded data —
 * everything comes from the schema.
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
        switch (comp.type) {
          case 'stats_grid':
            return <StatsGrid key={comp.id} components={comp.components ?? []} />;
          case 'activity_feed':
            return (
              <ActivityFeed
                key={comp.id}
                label={comp.label}
                items={comp.items ?? []}
              />
            );
          case 'quick_actions':
            return (
              <QuickActions
                key={comp.id}
                label={comp.label}
                items={comp.items ?? []}
              />
            );
          default:
            return (
              <Text key={comp.id} c="red" size="sm">
                Unknown dashboard component: {comp.type}
              </Text>
            );
        }
      })}
    </Stack>
  );
}
