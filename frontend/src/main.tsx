import '@mantine/core/styles.css';
import '@mantine/notifications/styles.css';
import './index.css';

import { MantineProvider, createTheme } from '@mantine/core';
import { Notifications } from '@mantine/notifications';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import { useThemeStore } from './state/themeStore';

function buildTheme(primaryColor: string, radius: string) {
  return createTheme({
    primaryColor,
    fontFamily: 'Inter, -apple-system, BlinkMacSystemFont, sans-serif',
    defaultRadius: radius,
    colors: {
      dark: [
        '#c9cdd5',
        '#a1a7b3',
        '#8b95a5',
        '#6b7280',
        '#4b5563',
        '#374151',
        '#1a2030',
        '#1e2536',
        '#1a1f2e',
        '#131720',
      ],
    },
    components: {
      Button: {
        defaultProps: { radius },
        styles: { root: { fontWeight: 600, fontSize: '13px' } },
      },
      TextInput: {
        styles: {
          label: { fontSize: '13px', fontWeight: 500, marginBottom: 4, color: '#94a3b8' },
          input: {
            background: 'rgba(255,255,255,0.04)',
            border: '1px solid rgba(255,255,255,0.08)',
            fontSize: '13px',
          },
        },
      },
      PasswordInput: {
        styles: {
          label: { fontSize: '13px', fontWeight: 500, marginBottom: 4, color: '#94a3b8' },
          input: {
            background: 'rgba(255,255,255,0.04)',
            border: '1px solid rgba(255,255,255,0.08)',
            fontSize: '13px',
          },
        },
      },
      NumberInput: {
        styles: {
          label: { fontSize: '13px', fontWeight: 500, marginBottom: 4, color: '#94a3b8' },
          input: {
            background: 'rgba(255,255,255,0.04)',
            border: '1px solid rgba(255,255,255,0.08)',
            fontSize: '13px',
          },
        },
      },
      Select: {
        styles: {
          label: { fontSize: '13px', fontWeight: 500, marginBottom: 4, color: '#94a3b8' },
          input: {
            background: 'rgba(255,255,255,0.04)',
            border: '1px solid rgba(255,255,255,0.08)',
            fontSize: '13px',
          },
        },
      },
      Modal: {
        styles: {
          content: { background: '#1a2030', border: '1px solid rgba(255,255,255,0.06)' },
          header: {
            background: '#1a2030',
            borderBottom: '1px solid rgba(255,255,255,0.06)',
            paddingBottom: 12,
          },
          title: { fontWeight: 600, fontSize: '15px' },
        },
      },
    },
  });
}

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      staleTime: 30_000,
    },
  },
});

function Root() {
  const primaryColor = useThemeStore((s) => s.primaryColor);
  const colorScheme = useThemeStore((s) => s.colorScheme);
  const radius = useThemeStore((s) => s.radius);
  const theme = buildTheme(primaryColor, radius);

  return (
    <MantineProvider theme={theme} defaultColorScheme={colorScheme}>
      <Notifications position="top-right" />
      <App />
    </MantineProvider>
  );
}

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      <Root />
    </QueryClientProvider>
  </React.StrictMode>
);
