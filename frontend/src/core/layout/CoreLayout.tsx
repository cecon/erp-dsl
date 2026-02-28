import { AppShell } from '@mantine/core';
import { useEffect } from 'react';
import { Header } from '../../components/layout/Header';
import { Sidebar } from '../../components/layout/Sidebar';
import { ThemeDrawer } from '../../components/layout/ThemeDrawer';
import { OttoPanel, useOttoContext } from '../../features/otto';
import { useThemeStore } from '../../state/themeStore';

interface CoreLayoutProps {
  children: React.ReactNode;
}

const SIDEBAR_WIDTH = 260;
const SIDEBAR_COLLAPSED_WIDTH = 80;
const OTTO_ASIDE_WIDTH = 400;

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

export function CoreLayout({ children }: CoreLayoutProps) {
  const collapsed = useThemeStore((s) => s.sidebarCollapsed);
  const primaryColor = useThemeStore((s) => s.primaryColor);
  const navWidth = collapsed ? SIDEBAR_COLLAPSED_WIDTH : SIDEBAR_WIDTH;
  const { opened: ottoOpened } = useOttoContext();

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
      aside={{
        width: OTTO_ASIDE_WIDTH,
        breakpoint: 'sm',
        collapsed: { desktop: !ottoOpened, mobile: !ottoOpened },
      }}
      padding="xl"
      transitionDuration={200}
      transitionTimingFunction="ease"
      styles={{
        main: {
          background: 'var(--content-bg)',
          minHeight: '100vh',
          transition: 'padding-inline-end 200ms ease',
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
        aside: {
          background: 'var(--card-bg)',
          borderLeft: '1px solid var(--border-default)',
          transition: 'width 200ms ease, transform 200ms ease',
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

      {ottoOpened && (
        <AppShell.Aside>
          <OttoPanel />
        </AppShell.Aside>
      )}

      <ThemeDrawer />
    </AppShell>
  );
}
