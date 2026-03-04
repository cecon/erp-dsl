import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface AuthState {
  token: string | null;
  accountId: string | null;
  email: string | null;
  name: string | null;
  login: (data: {
    access_token: string;
    account_id: string;
    email: string;
    name: string;
  }) => void;
  logout: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      token: null,
      accountId: null,
      email: null,
      name: null,
      login: (data) =>
        set({
          token: data.access_token,
          accountId: data.account_id,
          email: data.email,
          name: data.name,
        }),
      logout: () =>
        set({
          token: null,
          accountId: null,
          email: null,
          name: null,
        }),
    }),
    { name: 'platform-auth' }
  )
);
