import { create } from 'zustand';
import { persist } from 'zustand/middleware';

export type PrimaryColor = 'blue' | 'teal' | 'violet' | 'cyan' | 'orange' | 'indigo' | 'green';
export type RadiusSize = 'xs' | 'sm' | 'md' | 'lg' | 'xl';
export type FontSize = 'sm' | 'md' | 'lg';
export type ColorScheme = 'dark' | 'light';

interface ThemeState {
  primaryColor: PrimaryColor;
  colorScheme: ColorScheme;
  radius: RadiusSize;
  fontSize: FontSize;
  sidebarCollapsed: boolean;
  setPrimaryColor: (color: PrimaryColor) => void;
  setColorScheme: (scheme: ColorScheme) => void;
  toggleColorScheme: () => void;
  setRadius: (radius: RadiusSize) => void;
  setFontSize: (size: FontSize) => void;
  toggleSidebar: () => void;
}

export const useThemeStore = create<ThemeState>()(
  persist(
    (set) => ({
      primaryColor: 'blue',
      colorScheme: 'dark',
      radius: 'md',
      fontSize: 'md',
      sidebarCollapsed: false,
      setPrimaryColor: (primaryColor) => set({ primaryColor }),
      setColorScheme: (colorScheme) => set({ colorScheme }),
      toggleColorScheme: () =>
        set((s) => ({ colorScheme: s.colorScheme === 'dark' ? 'light' : 'dark' })),
      setRadius: (radius) => set({ radius }),
      setFontSize: (fontSize) => set({ fontSize }),
      toggleSidebar: () =>
        set((s) => ({ sidebarCollapsed: !s.sidebarCollapsed })),
    }),
    { name: 'erp-dsl-theme' }
  )
);
