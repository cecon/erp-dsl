/**
 * useOtto — SSE hook for the Otto universal chat.
 *
 * Uses fetch + ReadableStream (instead of EventSource) to support
 * POST requests with conversation history in the body.
 * Accumulates all session messages and sends the full history
 * on each new request for multi-turn context continuity.
 */

import { useCallback, useRef, useState } from 'react';
import { useAuthStore } from '../../state/authStore';
import type { OttoFormField, OttoMessage, OttoStatus } from './types';

let _msgId = 0;
function nextId(): string {
  return `otto-${++_msgId}-${Date.now()}`;
}

export interface UseOttoReturn {
  status: OttoStatus;
  messages: OttoMessage[];
  error: string | null;
  send: (message: string, pageKey?: string | null) => void;
  reset: () => void;
  submitForm: (messageId: string, values: Record<string, unknown>) => void;
}

/**
 * Build the conversation history from accumulated messages.
 * Only includes user and assistant messages (not tool, system, form).
 */
function buildHistory(messages: OttoMessage[]): Array<{ role: string; content: string }> {
  return messages
    .filter((m) => m.role === 'user' || m.role === 'assistant')
    .filter((m) => m.content && m.content.trim().length > 0)
    .map((m) => ({ role: m.role, content: m.content }));
}

/**
 * Parse SSE lines from a text chunk. Handles partial lines across chunks.
 */
function parseSSELines(text: string): Array<Record<string, unknown>> {
  const events: Array<Record<string, unknown>> = [];
  const lines = text.split('\n');
  for (const line of lines) {
    const trimmed = line.trim();
    if (trimmed.startsWith('data: ')) {
      try {
        events.push(JSON.parse(trimmed.slice(6)));
      } catch {
        // skip malformed
      }
    }
  }
  return events;
}

export function useOtto(): UseOttoReturn {
  const [status, setStatus] = useState<OttoStatus>('idle');
  const [messages, setMessages] = useState<OttoMessage[]>([]);
  const [error, setError] = useState<string | null>(null);
  const abortRef = useRef<AbortController | null>(null);

  const reset = useCallback(() => {
    abortRef.current?.abort();
    abortRef.current = null;
    setStatus('idle');
    setMessages([]);
    setError(null);
  }, []);

  /**
   * Core streaming function: sends POST with history and reads SSE stream.
   */
  const streamRequest = useCallback(async (
    input: string,
    currentMessages: OttoMessage[],
    pageKey?: string | null,
  ) => {
    abortRef.current?.abort();

    const controller = new AbortController();
    abortRef.current = controller;

    setStatus('streaming');
    setError(null);

    const token = useAuthStore.getState().token;
    const history = buildHistory(currentMessages);

    const url = `/api/otto/stream?token=${encodeURIComponent(token || '')}`;
    const body = JSON.stringify({
      input,
      page_key: pageKey || null,
      history,
    });

    try {
      const response = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body,
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
      let currentAssistantId: string | null = null;
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });

        // Process complete SSE events (separated by double newline)
        const parts = buffer.split('\n\n');
        buffer = parts.pop() || ''; // Keep incomplete part

        for (const part of parts) {
          const events = parseSSELines(part);
          for (const data of events) {
            // ── Form ────────────────────────────────────────
            if (data.role === 'form') {
              const formMsg: OttoMessage = {
                id: nextId(),
                role: 'form',
                content: (data.content as string) || 'Preencha os campos abaixo:',
                timestamp: Date.now(),
                formSchema: data.schema as OttoFormField[],
                formData: data.data as Record<string, unknown>,
              };
              setMessages((prev) => [...prev, formMsg]);
              setStatus('done');
              return;
            }

            // ── Component ────────────────────────────────────
            if (data.role === 'component') {
              const compMsg: OttoMessage = {
                id: nextId(),
                role: 'component',
                content: (data.content as string) || '',
                timestamp: Date.now(),
                componentName: data.component as string,
                componentProps: (data.props as Record<string, unknown>) || {},
              };
              setMessages((prev) => [...prev, compMsg]);
              if (data.done) {
                setStatus('done');
                return;
              }
              continue;
            }

            // ── Tool ────────────────────────────────────────
            if (data.role === 'tool') {
              const toolMsg: OttoMessage = {
                id: nextId(),
                role: 'tool',
                content: (data.content as string) || '',
                timestamp: Date.now(),
                toolName: data.tool_name as string,
                toolResult: data.tool_result,
              };
              setMessages((prev) => [...prev, toolMsg]);
              currentAssistantId = null;
              continue;
            }

            // ── System ──────────────────────────────────────
            if (data.role === 'system') {
              const sysMsg: OttoMessage = {
                id: nextId(),
                role: 'system',
                content: (data.content as string) || '',
                timestamp: Date.now(),
              };
              setMessages((prev) => [...prev, sysMsg]);
              if (data.done) {
                const ec = (data.content as string) || '';
                setStatus(ec.includes('Erro') ? 'error' : 'done');
                setError(ec.includes('Erro') ? ec : null);
                return;
              }
              continue;
            }

            // ── Assistant ───────────────────────────────────
            if (data.done) {
              if (data.content) {
                if (currentAssistantId) {
                  setMessages((prev) =>
                    prev.map((m) =>
                      m.id === currentAssistantId
                        ? { ...m, content: data.content as string, streaming: false }
                        : m
                    )
                  );
                } else {
                  setMessages((prev) => [
                    ...prev,
                    {
                      id: nextId(),
                      role: 'assistant' as const,
                      content: data.content as string,
                      timestamp: Date.now(),
                    },
                  ]);
                }
              }
              setStatus('done');
              currentAssistantId = null;
              return;
            }

            if (data.content) {
              if (currentAssistantId) {
                setMessages((prev) =>
                  prev.map((m) =>
                    m.id === currentAssistantId
                      ? { ...m, content: m.content + (data.content as string) }
                      : m
                  )
                );
              } else {
                const newId = nextId();
                currentAssistantId = newId;
                setMessages((prev) => [
                  ...prev,
                  {
                    id: newId,
                    role: 'assistant' as const,
                    content: data.content as string,
                    timestamp: Date.now(),
                    streaming: true,
                  },
                ]);
              }
            }
          }
        }
      }

      // Stream ended without explicit done
      setStatus('done');
    } catch (err: unknown) {
      if (err instanceof DOMException && err.name === 'AbortError') return;
      setError('Conexão com o servidor perdida.');
      setStatus('error');
    } finally {
      abortRef.current = null;
    }
  }, []);

  const send = useCallback((message: string, pageKey?: string | null) => {
    const userMsg: OttoMessage = {
      id: nextId(),
      role: 'user',
      content: message,
      timestamp: Date.now(),
    };

    setMessages((prev) => {
      const updated = [...prev, userMsg];
      // Trigger stream with the updated messages (including the new user msg)
      streamRequest(message, updated, pageKey);
      return updated;
    });
  }, [streamRequest]);

  const submitForm = useCallback((messageId: string, values: Record<string, unknown>) => {
    setMessages((prev) => {
      const updated = prev.map((m) =>
        m.id === messageId
          ? { ...m, formSubmitted: true, content: `Dados enviados: ${Object.keys(values).length} campos` }
          : m
      );

      const summary = Object.entries(values)
        .filter(([, v]) => v !== '' && v !== null && v !== undefined)
        .map(([k, v]) => `${k}: ${v}`)
        .join('\n');

      const userMsg: OttoMessage = {
        id: nextId(),
        role: 'user',
        content: summary || '(formulário enviado)',
        timestamp: Date.now(),
      };

      const withUserMsg = [...updated, userMsg];
      const formInput = `[FORM_RESPONSE] ${JSON.stringify(values)}`;
      streamRequest(formInput, withUserMsg);
      return withUserMsg;
    });
  }, [streamRequest]);

  return { status, messages, error, send, reset, submitForm };
}
