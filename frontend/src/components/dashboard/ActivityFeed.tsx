import { getIcon } from '../Icons';

/* eslint-disable @typescript-eslint/no-explicit-any */

interface ActivityItem {
  id: string;
  text: string;
  time: string;
  type?: string;
}

interface ActivityFeedProps {
  label: string;
  items: ActivityItem[];
}

/**
 * Recent activity feed rendered from DSL schema.
 * Displays a list of timestamped events with type-based icons.
 */
export function ActivityFeed({ label, items }: ActivityFeedProps) {
  return (
    <div className="admin-card activity-card">
      <div className="admin-card-header">
        <div className="admin-card-title">{label}</div>
      </div>
      <div className="activity-list">
        {items.map((item) => (
          <div key={item.id} className="activity-item">
            <span className="activity-icon">
              {getIcon(item.type)}
            </span>
            <div className="activity-content">
              <div className="activity-text">{item.text}</div>
              <div className="activity-time">{item.time}</div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
