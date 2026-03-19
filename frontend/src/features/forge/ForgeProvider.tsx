/**
 * ForgeProvider — React context for the Forge autonomous coding agent.
 */

import React, { createContext, useContext, useState } from 'react';
import { useForge } from './useForge';
import type { UseForgeReturn } from './useForge';

interface ForgeContextValue extends UseForgeReturn {
  opened: boolean;
  open: () => void;
  close: () => void;
  toggle: () => void;
}

const ForgeContext = createContext<ForgeContextValue | null>(null);

export function ForgeProvider({ children }: { children: React.ReactNode }) {
  const [opened, setOpened] = useState(false);
  const forge = useForge();

  const open = () => setOpened(true);
  const close = () => setOpened(false);
  const toggle = () => setOpened((v) => !v);

  return (
    <ForgeContext.Provider value={{ ...forge, opened, open, close, toggle }}>
      {children}
    </ForgeContext.Provider>
  );
}

export function useForgeContext(): ForgeContextValue {
  const ctx = useContext(ForgeContext);
  if (!ctx) throw new Error('useForgeContext must be used within ForgeProvider');
  return ctx;
}
