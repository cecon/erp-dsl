import { getIcon } from '../Icons';

/* eslint-disable @typescript-eslint/no-explicit-any */

interface StatCardProps {
  label: string;
  value: string;
  change?: string;
  trend?: 'up' | 'down';
  icon?: string;
}

/**
 * Dashboard stat card rendered from DSL schema.
 * Displays a metric with label, value, and optional trend indicator.
 */
export function StatCard({ label, value, change, trend, icon }: StatCardProps) {
  const trendClass = trend === 'up' ? 'stat-trend--up' : 'stat-trend--down';

  return (
    <div className="stat-card">
      <div className="stat-card-header">
        <span className="stat-card-icon">{getIcon(icon)}</span>
        <span className="stat-card-label">{label}</span>
      </div>
      <div className="stat-card-value">{value}</div>
      {change && (
        <div className={`stat-card-trend ${trendClass}`}>
          {trend === 'up' ? '↑' : '↓'} {change}
        </div>
      )}
    </div>
  );
}

interface StatsGridProps {
  components: any[];
}

export function StatsGrid({ components }: StatsGridProps) {
  return (
    <div className="stats-grid">
      {components.map((stat: any) => (
        <StatCard
          key={stat.id}
          label={stat.label}
          value={stat.value}
          change={stat.change}
          trend={stat.trend}
          icon={stat.icon}
        />
      ))}
    </div>
  );
}
