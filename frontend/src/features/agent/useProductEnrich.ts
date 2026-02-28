/**
 * useProductEnrich — SSE hook for the product-enrich agent.
 *
 * Manages connection lifecycle, step accumulation, draft state,
 * and exposes a simple start / reset API to the UI layer.
 */

import { useCallback, useRef, useState } from 'react';
import { useAuthStore } from '../../state/authStore';

/* ── Types ────────────────────────────────────────────────────────── */

export interface AgentStep {
  iteration: number;
  step: string;           // 'skill_call' | 'parse_error' | 'invalid_action' | …
  skill?: string;         // e.g. 'fetch_by_ean', 'classify_ncm'
  result?: Record<string, unknown>;
  done: boolean;
  error?: string;
  draft?: Record<string, unknown>;
}

export type EnrichStatus = 'idle' | 'streaming' | 'done' | 'error';

export interface UseProductEnrichReturn {
  status: EnrichStatus;
  steps: AgentStep[];
  draft: Record<string, unknown> | null;
  error: string | null;
  start: (userInput: string) => void;
  reset: () => void;
}

/* ── Hook ─────────────────────────────────────────────────────────── */

export function useProductEnrich(): UseProductEnrichReturn {
  const [status, setStatus] = useState<EnrichStatus>('idle');
  const [steps, setSteps] = useState<AgentStep[]>([]);
  const [draft, setDraft] = useState<Record<string, unknown> | null>(null);
  const [error, setError] = useState<string | null>(null);
  const esRef = useRef<EventSource | null>(null);

  const reset = useCallback(() => {
    esRef.current?.close();
    esRef.current = null;
    setStatus('idle');
    setSteps([]);
    setDraft(null);
    setError(null);
  }, []);

  const start = useCallback((userInput: string) => {
    // Close any previous connection
    esRef.current?.close();

    setStatus('streaming');
    setSteps([]);
    setDraft(null);
    setError(null);

    const token = useAuthStore.getState().token;
    const params = new URLSearchParams({
      user_input: userInput,
      ...(token ? { token } : {}),
    });

    const url = `/api/agent/product-enrich/stream?${params.toString()}`;
    const es = new EventSource(url);
    esRef.current = es;

    es.onmessage = (event) => {
      try {
        const data: AgentStep = JSON.parse(event.data);

        if (data.done) {
          if (data.error) {
            setError(data.error);
            setStatus('error');
          } else {
            setDraft(data.draft ?? null);
            setStatus('done');
          }
          // Add final step to timeline
          setSteps((prev) => [...prev, data]);
          es.close();
          esRef.current = null;
          return;
        }

        // In-progress step
        setSteps((prev) => [...prev, data]);
      } catch {
        // ignore malformed events
      }
    };

    es.onerror = () => {
      setError('Conexão com o servidor perdida.');
      setStatus('error');
      es.close();
      esRef.current = null;
    };
  }, []);

  return { status, steps, draft, error, start, reset };
}
