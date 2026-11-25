import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';

type Theme = 'light' | 'dark' | 'system';

interface ThemeState {
  theme: Theme;
  resolvedTheme: 'light' | 'dark';
  setTheme: (theme: Theme) => void;
  initializeTheme: () => void;
}

export const useThemeStore = create<ThemeState>()(
  persist(
    (set, get) => ({
      theme: 'system',
      resolvedTheme: 'light',

      setTheme: (theme: Theme) => {
        set({ theme });
        get().applyTheme(theme);
      },

      initializeTheme: () => {
        const { theme } = get();
        get().applyTheme(theme);
      },

      applyTheme: (theme: Theme) => {
        let resolved: 'light' | 'dark' = 'light';

        if (theme === 'system') {
          resolved = window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
        } else {
          resolved = theme;
        }

        set({ resolvedTheme: resolved });
        document.documentElement.setAttribute('data-theme', resolved);

        // Update meta theme-color
        const metaThemeColor = document.querySelector('meta[name="theme-color"]');
        if (metaThemeColor) {
          metaThemeColor.setAttribute('content', resolved === 'dark' ? '#1E1B4B' : '#6366F1');
        }
      },
    }),
    {
      name: 'theme-storage',
      storage: createJSONStorage(() => localStorage),
      partialize: (state) => ({ theme: state.theme }),
      onRehydrateStorage: () => (state) => {
        if (state) {
          state.initializeTheme();

          // Listen for system theme changes
          if (state.theme === 'system') {
            const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
            const handler = (e: MediaQueryListEvent) => {
              state.applyTheme('system');
            };
            mediaQuery.addEventListener('change', handler);

            // Store cleanup function
            (window as any).__themeCleanup = () => mediaQuery.removeEventListener('change', handler);
          }
        }
      },
    }
  )
);

// Initialize theme on load
if (typeof window !== 'undefined') {
  useThemeStore.getState().initializeTheme();
}

export const useTheme = () => useThemeStore();