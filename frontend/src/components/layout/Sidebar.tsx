import { Loader, Text, Tooltip } from '@mantine/core';
import { useQuery } from '@tanstack/react-query';
import { useCallback, useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import api from '../../services/api';
import { useThemeStore } from '../../state/themeStore';
import { getIcon } from '../Icons';

/* eslint-disable @typescript-eslint/no-explicit-any */

/**
 * DSL-driven sidebar. Fetches navigation schema from the backend
 * and renders sections/items dynamically. Supports collapsed mode
 * and collapsible submenu sections.
 */
export function Sidebar() {
  const navigate = useNavigate();
  const location = useLocation();
  const collapsed = useThemeStore((s) => s.sidebarCollapsed);
  const [openSections, setOpenSections] = useState<Record<string, boolean>>({});

  const { data, isLoading } = useQuery({
    queryKey: ['page', '_sidebar'],
    queryFn: () => api.get('/pages/_sidebar').then((r) => r.data),
    staleTime: 60_000,
  });

  const schema = data?.schema;

  const toggleSection = useCallback((sectionId: string) => {
    setOpenSections((prev) => ({ ...prev, [sectionId]: !prev[sectionId] }));
  }, []);

  const isSectionActive = (section: any) =>
    section.items?.some((item: any) => location.pathname === item.path);

  const renderNavItem = (item: any, indented = false) => {
    const isActive = location.pathname === item.path;
    return (
      <Tooltip key={item.id} label={item.label} position="right" disabled={!collapsed}>
        <div
          className={`sidebar-item ${isActive ? 'active' : ''} ${indented ? 'sidebar-subitem' : ''}`}
          onClick={() => navigate(item.path)}
        >
          <span className="sidebar-item-icon">{getIcon(item.icon)}</span>
          {!collapsed && item.label}
        </div>
      </Tooltip>
    );
  };

  const renderSection = (section: any) => {
    // "main" section or single-item sections render flat (no collapsible)
    if (section.id === 'main' || (section.items?.length ?? 0) <= 1) {
      return (
        <div key={section.id}>
          {!collapsed && (
            <div className="sidebar-section-label">{section.label}</div>
          )}
          {section.items?.map((item: any) => renderNavItem(item))}
        </div>
      );
    }

    // Multi-item sections render as collapsible menus
    const isOpen = openSections[section.id] ?? isSectionActive(section);
    const hasActive = isSectionActive(section);

    return (
      <div key={section.id} className="sidebar-section-collapsible">
        {collapsed ? (
          // When collapsed, show items directly with tooltips
          section.items?.map((item: any) => renderNavItem(item))
        ) : (
          <>
            <div
              className={`sidebar-section-toggle ${hasActive ? 'has-active' : ''}`}
              onClick={() => toggleSection(section.id)}
            >
              <span className="sidebar-section-toggle-label">
                {section.label}
              </span>
              <span className={`sidebar-chevron ${isOpen ? 'open' : ''}`}>
                ›
              </span>
            </div>
            <div className={`sidebar-submenu ${isOpen ? 'open' : ''}`}>
              {section.items?.map((item: any) => renderNavItem(item, true))}
            </div>
          </>
        )}
      </div>
    );
  };

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
          schema?.sections?.map((section: any) => renderSection(section))
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
