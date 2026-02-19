import { Loader, Text, Tooltip } from '@mantine/core';
import { useQuery } from '@tanstack/react-query';
import { useNavigate, useLocation } from 'react-router-dom';
import api from '../../services/api';
import { useThemeStore } from '../../state/themeStore';
import { getIcon } from '../Icons';

/* eslint-disable @typescript-eslint/no-explicit-any */

/**
 * DSL-driven sidebar. Fetches navigation schema from the backend
 * and renders sections/items dynamically. Supports collapsed mode.
 */
export function Sidebar() {
  const navigate = useNavigate();
  const location = useLocation();
  const collapsed = useThemeStore((s) => s.sidebarCollapsed);

  const { data, isLoading } = useQuery({
    queryKey: ['page', '_sidebar'],
    queryFn: () => api.get('/pages/_sidebar').then((r) => r.data),
    staleTime: 60_000,
  });

  const schema = data?.schema;

  return (
    <div className={`admin-sidebar ${collapsed ? 'sidebar-collapsed' : ''}`}>
      {/* Brand */}
      <div className="sidebar-brand">
        <div className="sidebar-brand-icon">
          {schema?.brand?.icon ?? 'E'}
        </div>
        {!collapsed && (
          <div className="sidebar-brand-text">
            {schema?.brand?.text ?? 'ERP-DSL'}
          </div>
        )}
      </div>

      {/* Navigation */}
      <nav className="sidebar-nav">
        {isLoading ? (
          <div style={{ padding: 16, textAlign: 'center' }}>
            <Loader size="xs" />
          </div>
        ) : (
          schema?.sections?.map((section: any) => (
            <div key={section.id}>
              {!collapsed && (
                <div className="sidebar-section-label">{section.label}</div>
              )}
              {section.items?.map((item: any) => {
                const isActive = location.pathname === item.path;

                return (
                  <Tooltip
                    key={item.id}
                    label={item.label}
                    position="right"
                    disabled={!collapsed}
                  >
                    <div
                      className={`sidebar-item ${isActive ? 'active' : ''}`}
                      onClick={() => navigate(item.path)}
                    >
                      <span className="sidebar-item-icon">{getIcon(item.icon)}</span>
                      {!collapsed && item.label}
                    </div>
                  </Tooltip>
                );
              })}
            </div>
          ))
        )}
      </nav>

      {/* Footer */}
      <div className="sidebar-footer">
        {!collapsed && (
          <Text size="xs" c="dimmed">
            {schema?.footer?.text ?? 'ERP-DSL Platform'}
          </Text>
        )}
      </div>
    </div>
  );
}
