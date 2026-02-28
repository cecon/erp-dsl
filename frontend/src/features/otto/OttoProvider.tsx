/**
 * OttoProvider — global context provider for the Otto chat.
 */

import {
  createContext,
  useCallback,
  useContext,
  useState,
  type ReactNode,
} from 'react';
import { useOtto, type UseOttoReturn } from './useOtto';
import type { OttoContext } from './types';

/* ── Context shape ───────────────────────────────────────────────── */

interface OttoContextValue extends UseOttoReturn {
  opened: boolean;
  toggle: () => void;
  open: () => void;
  close: () => void;
  context: OttoContext;
  setContext: (ctx: Partial<OttoContext>) => void;
}

const OttoCtx = createContext<OttoContextValue | null>(null);

/* ── Hook to consume ─────────────────────────────────────────────── */

export function useOttoContext(): OttoContextValue {
  const ctx = useContext(OttoCtx);
  if (!ctx) {
    throw new Error('useOttoContext must be used inside <OttoProvider>');
  }
  return ctx;
}

/* ── Provider component ──────────────────────────────────────────── */

interface OttoProviderProps {
  children: ReactNode;
}

export function OttoProvider({ children }: OttoProviderProps) {
  const [opened, setOpened] = useState(false);
  const [context, setContextState] = useState<OttoContext>({
    pageKey: null,
    pageTitle: null,
    entityEndpoint: null,
  });

  const chat = useOtto();

  const toggle = useCallback(() => setOpened((o) => !o), []);
  const open = useCallback(() => setOpened(true), []);
  const close = useCallback(() => setOpened(false), []);

  const setContext = useCallback((partial: Partial<OttoContext>) => {
    setContextState((prev) => ({ ...prev, ...partial }));
  }, []);

  const value: OttoContextValue = {
    opened,
    toggle,
    open,
    close,
    context,
    setContext,
    ...chat,
  };

  return <OttoCtx.Provider value={value}>{children}</OttoCtx.Provider>;
}
