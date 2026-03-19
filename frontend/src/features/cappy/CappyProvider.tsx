/**
 * CappyProvider — React context for the Cappy autonomous coding agent.
 */

import React, { createContext, useContext, useState } from 'react';
import { useCappy } from './useCappy';
import type { UseCappyReturn } from './useCappy';

interface CappyContextValue extends UseCappyReturn {
  opened: boolean;
  open: () => void;
  close: () => void;
  toggle: () => void;
}

const CappyContext = createContext<CappyContextValue | null>(null);

export function CappyProvider({ children }: { children: React.ReactNode }) {
  const [opened, setOpened] = useState(false);
  const cappy = useCappy();

  const open = () => setOpened(true);
  const close = () => setOpened(false);
  const toggle = () => setOpened((v) => !v);

  return (
    <CappyContext.Provider value={{ ...cappy, opened, open, close, toggle }}>
      {children}
    </CappyContext.Provider>
  );
}

export function useCappyContext(): CappyContextValue {
  const ctx = useContext(CappyContext);
  if (!ctx) throw new Error('useCappyContext must be used within CappyProvider');
  return ctx;
}
