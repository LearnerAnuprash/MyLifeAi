import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';
import { graphqlRequest } from '@/utils/graphqlClient';
import type { User, AuthPayload } from '@/types/graphql';
import { ME_QUERY, REFRESH_TOKEN_MUTATION } from "@/graphql/operations";

interface AuthState {
  user: User | null;
  accessToken: string | null;
  refreshToken: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;

  // Actions
  setAuth: (payload: AuthPayload) => void;
  setUser: (user: User) => void;
  setTokens: (accessToken: string, refreshToken: string) => void;
  logout: () => void;
  checkAuth: () => Promise<void>;
  refreshAccessToken: () => Promise<boolean>;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      user: null,
      accessToken: null,
      refreshToken: null,
      isAuthenticated: false,
      isLoading: true,

      setAuth: (payload: AuthPayload) => {
        set({
          user: payload.user,
          accessToken: payload.token,
          refreshToken: payload.refreshToken,
          isAuthenticated: true,
          isLoading: false,
        });
      },

      setUser: (user: User) => {
        set({ user });
      },

      setTokens: (accessToken: string, refreshToken: string) => {
        set({ accessToken, refreshToken });
      },

      logout: () => {
        set({
          user: null,
          accessToken: null,
          refreshToken: null,
          isAuthenticated: false,
        });
      },

      checkAuth: async () => {
        const { accessToken } = get();

        if (!accessToken) {
          set({ isLoading: false, isAuthenticated: false });
          return;
        }

        try {
          const response = await graphqlRequest<{ me: User }>(ME_QUERY, {}, accessToken);

          if (response.data?.me) {
            set({
              user: response.data.me,
              isAuthenticated: true,
              isLoading: false,
            });
          } else {
            // Token might be expired, try refresh
            const refreshed = await get().refreshAccessToken();
            if (!refreshed) {
              set({ isLoading: false, isAuthenticated: false });
            }
          }
        } catch (error) {
          console.error('Auth check failed:', error);
          // Try refresh token
          const refreshed = await get().refreshAccessToken();
          if (!refreshed) {
            set({ isLoading: false, isAuthenticated: false });
          }
        }
      },

      refreshAccessToken: async () => {
        const { refreshToken } = get();

        if (!refreshToken) {
          return false;
        }

        try {
          const response = await graphqlRequest<{ refreshToken: string }>(
            REFRESH_TOKEN_MUTATION,
            {},
            { refreshToken }
          );

          if (response.data?.refreshToken) {
            set({ accessToken: response.data.refreshToken });
            return true;
          }
        } catch (error) {
          console.error('Token refresh failed:', error);
        }

        // Refresh failed, logout
        get().logout();
        return false;
      },
    }),
    {
      name: 'auth-storage',
      storage: createJSONStorage(() => localStorage),
      partialize: (state) => ({
        accessToken: state.accessToken,
        refreshToken: state.refreshToken,
      }),
    }
  )
);

// Initialize auth on app load
if (typeof window !== 'undefined') {
  useAuthStore.getState().checkAuth();
}

export const useAuth = () => useAuthStore();