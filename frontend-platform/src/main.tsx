import '@mantine/core/styles.css';
import '@mantine/notifications/styles.css';
import './index.css';

import { MantineProvider, createTheme } from '@mantine/core';
import { Notifications } from '@mantine/notifications';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';

const theme = createTheme({
  primaryColor: 'indigo',
  fontFamily: 'Inter, -apple-system, BlinkMacSystemFont, sans-serif',
  defaultRadius: 'md',
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
      defaultProps: { radius: 'md' },
      styles: { root: { fontWeight: 600, fontSize: '13px' } },
    },
    TextInput: {
      styles: {
        label: {
          fontSize: '13px',
          fontWeight: 500,
          marginBottom: 4,
          color: 'var(--input-label)',
        },
        input: {
          background: 'var(--input-bg)',
          border: '1px solid var(--input-border)',
          fontSize: '13px',
        },
      },
    },
    PasswordInput: {
      styles: {
        label: {
          fontSize: '13px',
          fontWeight: 500,
          marginBottom: 4,
          color: 'var(--input-label)',
        },
        input: {
          background: 'var(--input-bg)',
          border: '1px solid var(--input-border)',
          fontSize: '13px',
        },
      },
    },
    Modal: {
      styles: {
        content: {
          background: 'var(--card-bg)',
          border: '1px solid var(--border-default)',
        },
        header: {
          background: 'var(--card-bg)',
          borderBottom: '1px solid var(--border-default)',
          paddingBottom: 12,
        },
        title: { fontWeight: 600, fontSize: '15px' },
      },
    },
  },
});

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { retry: 1, staleTime: 30_000 },
  },
});

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      <MantineProvider theme={theme} defaultColorScheme="dark">
        <Notifications position="top-right" />
        <App />
      </MantineProvider>
    </QueryClientProvider>
  </React.StrictMode>
);
