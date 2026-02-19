import { ActionIcon, Menu, TextInput, Tooltip } from '@mantine/core';
import { useQuery } from '@tanstack/react-query';
import { useLocation } from 'react-router-dom';
import api from '../../services/api';
import { useAuthStore } from '../../state/authStore';
import { useThemeStore } from '../../state/themeStore';

/* eslint-disable @typescript-eslint/no-explicit-any */

/**
 * DSL-driven header. Fetches config from backend _header schema.
 * Renders breadcrumbs, search, notifications, user area, and
 * sidebar toggle + gear icon for theme drawer.
 */
export function Header() {
  const username = useAuthStore((s) => s.username);
  const role = useAuthStore((s) => s.role);
  const logout = useAuthStore((s) => s.logout);
  const toggleSidebar = useThemeStore((s) => s.toggleSidebar);
  const location = useLocation();

  const { data } = useQuery({
    queryKey: ['page', '_header'],
    queryFn: () => api.get('/pages/_header').then((r) => r.data),
    staleTime: 60_000,
  });

  const schema = data?.schema;
  const searchEnabled = schema?.search?.enabled ?? true;
  const initials = (username || 'U').substring(0, 2).toUpperCase();

  // Build breadcrumb from current path
  const pathSegments = location.pathname.split('/').filter(Boolean);
  const breadcrumb = pathSegments.length > 0
    ? pathSegments.map((s) => s.charAt(0).toUpperCase() + s.slice(1)).join(' / ')
    : 'Dashboard';

  return (
    <div className="admin-header">
      <div className="header-left">
        <Tooltip label="Toggle sidebar" position="bottom">
          <ActionIcon
            variant="subtle"
            color="gray"
            size="lg"
            onClick={toggleSidebar}
          >
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
              <line x1="3" y1="6" x2="21" y2="6" />
              <line x1="3" y1="12" x2="21" y2="12" />
              <line x1="3" y1="18" x2="21" y2="18" />
            </svg>
          </ActionIcon>
        </Tooltip>
        <div className="header-breadcrumb">{breadcrumb}</div>
        {searchEnabled && (
          <TextInput
            placeholder={schema?.search?.placeholder ?? 'Search…'}
            size="xs"
            variant="filled"
            className="header-search"
            styles={{
              input: {
                background: 'var(--input-bg)',
                border: '1px solid var(--input-border)',
                width: 220,
              },
            }}
          />
        )}
      </div>

      <div className="header-right">
        {/* Notifications */}
        <Tooltip label="Notifications" position="bottom">
          <ActionIcon variant="subtle" color="gray" size="lg">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9" />
              <path d="M13.73 21a2 2 0 0 1-3.46 0" />
            </svg>
          </ActionIcon>
        </Tooltip>

        {/* User Menu Dropdown */}
        <Menu shadow="md" width={200} position="bottom-end">
          <Menu.Target>
            <div className="header-user">
              <div className="header-avatar">{initials}</div>
              <div className="header-user-info">
                <div className="header-user-name">{username}</div>
                <div className="header-user-role">{role}</div>
              </div>
            </div>
          </Menu.Target>
          <Menu.Dropdown>
            <Menu.Label>Account</Menu.Label>
            <Menu.Item>Profile</Menu.Item>
            <Menu.Item>Settings</Menu.Item>
            <Menu.Divider />
            <Menu.Item
              color="red"
              onClick={() => {
                logout();
                window.location.href = '/login';
              }}
            >
              Logout
            </Menu.Item>
          </Menu.Dropdown>
        </Menu>
      </div>
    </div>
  );
}
