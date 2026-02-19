import { useNavigate } from 'react-router-dom';
import { getIcon } from '../Icons';

/* eslint-disable @typescript-eslint/no-explicit-any */

interface QuickAction {
  id: string;
  label: string;
  icon?: string;
  action?: { type: string; to?: string };
}

interface QuickActionsProps {
  label: string;
  items: QuickAction[];
}

/**
 * Quick action buttons rendered from DSL schema.
 * Supports the whitelisted 'navigate' action type.
 */
export function QuickActions({ label, items }: QuickActionsProps) {
  const navigate = useNavigate();

  const handleClick = (action?: { type: string; to?: string }) => {
    if (!action) return;
    if (action.type === 'navigate' && action.to) {
      navigate(action.to);
    }
  };

  return (
    <div className="admin-card quick-actions-card">
      <div className="admin-card-header">
        <div className="admin-card-title">{label}</div>
      </div>
      <div className="quick-actions-grid">
        {items.map((item) => (
          <button
            key={item.id}
            className="quick-action-btn"
            onClick={() => handleClick(item.action)}
          >
            <span className="quick-action-icon">
              {getIcon(item.icon)}
            </span>
            <span className="quick-action-label">{item.label}</span>
          </button>
        ))}
      </div>
    </div>
  );
}
