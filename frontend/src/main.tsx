import React from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ConfigProvider } from 'antd';

import App from './App';
import { useThemeStore } from './store/themeStore';
import './styles/globals.css';

// Initialize theme on load
useThemeStore.getState().initializeTheme();

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 5, // 5 minutes
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
});

// Custom Ant Design theme
const antdTheme = {
  token: {
    colorPrimary: '#6366F1',
    colorSuccess: '#22C55E',
    colorWarning: '#F59E0B',
    colorError: '#EF4444',
    borderRadius: 8,
    fontFamily: 'Inter, system-ui, sans-serif',
    controlHeight: 44,
    fontSize: 14,
  },
  components: {
    Button: {
      controlHeight: 44,
      fontWeight: 500,
      borderRadius: 8,
    },
    Input: {
      controlHeight: 44,
      paddingInline: 12,
      borderRadius: 8,
    },
    Select: {
      controlHeight: 44,
      borderRadius: 8,
    },
    DatePicker: {
      controlHeight: 44,
      borderRadius: 8,
    },
    Modal: {
      borderRadius: 12,
      contentBg: 'var(--color-bg-secondary)',
    },
    Card: {
      borderRadius: 12,
      boxShadow: '0 1px 3px 0 rgb(0 0 0 / 0.1)',
    },
    Dropdown: {
      borderRadius: 8,
    },
    Tooltip: {
      borderRadius: 6,
    },
    Tag: {
      borderRadius: 6,
    },
  },
  algorithm: undefined, // Use default algorithm
};

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <ConfigProvider theme={antdTheme}>
          <App />
        </ConfigProvider>
      </BrowserRouter>
    </QueryClientProvider>
  </React.StrictMode>
);