import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface AuthState {
  token: string | null;
  tenantId: string | null;
  username: string | null;
  role: string | null;
  login: (data: {
    access_token: string;
    tenant_id: string;
    username: string;
    role: string;
  }) => void;
  logout: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      token: null,
      tenantId: null,
      username: null,
      role: null,
      login: (data) =>
        set({
          token: data.access_token,
          tenantId: data.tenant_id,
          username: data.username,
          role: data.role,
        }),
      logout: () =>
        set({
          token: null,
          tenantId: null,
          username: null,
          role: null,
        }),
    }),
    { name: 'erp-dsl-auth' }
  )
);
