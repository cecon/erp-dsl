/**
 * useForge — SSE hook for the Forge autonomous coding agent.
 *
 * Connects to POST /forge/stream and streams back log events
 * as the agent clones the repo, makes changes, and opens a PR.
 */

import { useCallback, useRef, useState } from 'react';
import { useAuthStore } from '../../state/authStore';
import type { ForgeEvent, ForgeMessage, ForgeStatus } from './types';

let _msgId = 0;
function nextId(): string {
  return `forge-${++_msgId}-${Date.now()}`;
}

export interface UseForgeReturn {
  status: ForgeStatus;
  messages: ForgeMessage[];
  prUrl: string | null;
  error: string | null;
  send: (task: string) => void;
  reset: () => void;
}

export function useForge(): UseForgeReturn {
  const [status, setStatus] = useState<ForgeStatus>('idle');
  const [messages, setMessages] = useState<ForgeMessage[]>([]);
  const [prUrl, setPrUrl] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const abortRef = useRef<AbortController | null>(null);

  const reset = useCallback(() => {
    abortRef.current?.abort();
    abortRef.current = null;
    setStatus('idle');
    setMessages([]);
    setPrUrl(null);
    setError(null);
  }, []);

  const addMessage = useCallback((event: ForgeEvent) => {
    const msg: ForgeMessage = {
      id: nextId(),
      type: event.type,
      category: event.category || 'info',
      message: event.message || '',
      timestamp: Date.now(),
      prUrl: event.pr_url,
    };
    setMessages((prev) => [...prev, msg]);
    return msg;
  }, []);

  const send = useCallback((task: string) => {
    // Reset state
    abortRef.current?.abort();
    const controller = new AbortController();
    abortRef.current = controller;

    setStatus('streaming');
    setError(null);
    setPrUrl(null);
    setMessages([
      {
        id: nextId(),
        type: 'log',
        category: 'status',
        message: `🚀 Iniciando tarefa: ${task}`,
        timestamp: Date.now(),
      },
    ]);

    const token = useAuthStore.getState().token;
    const url = `/api/forge/stream?token=${encodeURIComponent(token || '')}`;

    (async () => {
      try {
        const response = await fetch(url, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ task }),
          signal: controller.signal,
        });

        if (!response.ok) {
          const errText = await response.text().catch(() => response.statusText);
          setError(`Erro ${response.status}: ${errText}`);
          setStatus('error');
          return;
        }

        const reader = response.body?.getReader();
        if (!reader) {
          setError('Stream não disponível');
          setStatus('error');
          return;
        }

        const decoder = new TextDecoder();
        let buffer = '';

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });
          const parts = buffer.split('\n\n');
          buffer = parts.pop() || '';

          for (const part of parts) {
            const line = part.trim();
            if (!line.startsWith('data: ')) continue;

            try {
              const event: ForgeEvent = JSON.parse(line.slice(6));

              if (event.type === 'heartbeat') continue;

              addMessage(event);

              if (event.type === 'done') {
                if (event.pr_url) setPrUrl(event.pr_url);
                setStatus('done');
                return;
              }

              if (event.type === 'error') {
                setError(event.message || 'Erro desconhecido');
                setStatus('error');
                return;
              }
            } catch {
              // skip malformed
            }
          }
        }

        setStatus('done');
      } catch (err: unknown) {
        if (err instanceof DOMException && err.name === 'AbortError') return;
        setError('Conexão com o servidor perdida.');
        setStatus('error');
      } finally {
        abortRef.current = null;
      }
    })();
  }, [addMessage]);

  return { status, messages, prUrl, error, send, reset };
}
