import { AppShell, Drawer } from '@mantine/core';
import { useCallback, useEffect, useRef, useState } from 'react';
import { Header } from '../../components/layout/Header';
import { Sidebar } from '../../components/layout/Sidebar';
import { ThemeDrawer } from '../../components/layout/ThemeDrawer';
import { OttoPanel } from '../../features/otto/OttoPanel';
import { useOttoContext } from '../../features/otto';
import { useThemeStore } from '../../state/themeStore';

interface CoreLayoutProps {
  children: React.ReactNode;
}

const SIDEBAR_WIDTH = 260;
const SIDEBAR_COLLAPSED_WIDTH = 80;
const DRAWER_MIN_WIDTH = 360;
const DRAWER_MAX_WIDTH = 1200;
const DRAWER_DEFAULT_WIDTH = 520;
const DRAWER_STORAGE_KEY = 'otto-drawer-width';

/** Maps Mantine color names to their primary hex values for CSS custom props. */
const COLOR_HEX: Record<string, string> = {
  blue: '#3b82f6',
  teal: '#14b8a6',
  violet: '#8b5cf6',
  cyan: '#06b6d4',
  orange: '#f97316',
  indigo: '#6366f1',
  green: '#22c55e',
};

function getStoredWidth(): number {
  try {
    const stored = localStorage.getItem(DRAWER_STORAGE_KEY);
    if (stored) {
      const w = parseInt(stored, 10);
      if (w >= DRAWER_MIN_WIDTH && w <= DRAWER_MAX_WIDTH) return w;
    }
  } catch { /* ignore */ }
  return DRAWER_DEFAULT_WIDTH;
}

export function CoreLayout({ children }: CoreLayoutProps) {
  const collapsed = useThemeStore((s) => s.sidebarCollapsed);
  const primaryColor = useThemeStore((s) => s.primaryColor);
  const navWidth = collapsed ? SIDEBAR_COLLAPSED_WIDTH : SIDEBAR_WIDTH;
  const { opened: ottoOpened, close: closeOtto } = useOttoContext();

  const [drawerWidth, setDrawerWidth] = useState(getStoredWidth);
  const isDragging = useRef(false);

  const handleMouseDown = useCallback((e: React.MouseEvent) => {
    e.preventDefault();
    isDragging.current = true;
    document.body.style.cursor = 'col-resize';
    document.body.style.userSelect = 'none';

    const onMouseMove = (ev: MouseEvent) => {
      if (!isDragging.current) return;
      const newWidth = Math.min(DRAWER_MAX_WIDTH, Math.max(DRAWER_MIN_WIDTH, window.innerWidth - ev.clientX));
      setDrawerWidth(newWidth);
    };

    const onMouseUp = () => {
      isDragging.current = false;
      document.body.style.cursor = '';
      document.body.style.userSelect = '';
      document.removeEventListener('mousemove', onMouseMove);
      document.removeEventListener('mouseup', onMouseUp);
      // Persist
      setDrawerWidth((w) => {
        localStorage.setItem(DRAWER_STORAGE_KEY, String(w));
        return w;
      });
    };

    document.addEventListener('mousemove', onMouseMove);
    document.addEventListener('mouseup', onMouseUp);
  }, []);

  // Sync CSS custom property with selected theme color
  useEffect(() => {
    const hex = COLOR_HEX[primaryColor] ?? '#3b82f6';
    document.documentElement.style.setProperty('--accent', hex);
    document.documentElement.style.setProperty('--accent-hover', hex);
    document.documentElement.style.setProperty('--accent-subtle', `${hex}1a`);
    document.documentElement.style.setProperty('--sidebar-active', `${hex}1f`);
    document.documentElement.style.setProperty('--sidebar-active-border', hex);
    document.documentElement.style.setProperty('--card-hover-border', `${hex}40`);
  }, [primaryColor]);

  return (
    <AppShell
      header={{ height: 56 }}
      navbar={{ width: navWidth, breakpoint: 'sm' }}
      padding="xl"
      transitionDuration={200}
      transitionTimingFunction="ease"
      styles={{
        main: {
          background: 'var(--content-bg)',
          minHeight: '100vh',
        },
        header: {
          background: 'var(--header-bg)',
          borderBottom: '1px solid var(--header-border)',
        },
        navbar: {
          background: 'var(--sidebar-bg)',
          borderRight: 'none',
          transition: 'width 200ms ease',
        },
      }}
    >
      <AppShell.Header>
        <Header />
      </AppShell.Header>

      <AppShell.Navbar>
        <Sidebar />
      </AppShell.Navbar>

      <AppShell.Main>
        <div className="fade-in">{children}</div>
      </AppShell.Main>

      {/* Otto Chat — Drawer resizável */}
      <Drawer
        opened={ottoOpened}
        onClose={closeOtto}
        position="right"
        size={drawerWidth}
        withCloseButton={false}
        overlayProps={{ backgroundOpacity: 0.3, blur: 2 }}
        transitionProps={{ duration: 200 }}
        styles={{
          body: { padding: 0, height: '100%' },
          content: { background: 'var(--card-bg, #1a1f2e)', overflow: 'visible' },
        }}
      >
        {/* Resize handle */}
        <div
          onMouseDown={handleMouseDown}
          style={{
            position: 'absolute',
            left: 0,
            top: 0,
            bottom: 0,
            width: 5,
            cursor: 'col-resize',
            zIndex: 10,
            background: 'transparent',
          }}
          onMouseEnter={(e) => {
            (e.target as HTMLElement).style.background = 'var(--accent, #6366f1)';
            (e.target as HTMLElement).style.opacity = '0.5';
          }}
          onMouseLeave={(e) => {
            if (!isDragging.current) {
              (e.target as HTMLElement).style.background = 'transparent';
              (e.target as HTMLElement).style.opacity = '1';
            }
          }}
        />
        <OttoPanel />
      </Drawer>

      <ThemeDrawer />
    </AppShell>
  );
}
