/**
 * WorkflowTester — inline sandbox tester for a saved workflow.
 *
 * Renders inside the workflow form page:
 * - Text input + "▶ Testar" button
 * - SSE stream from POST /workflows/{id}/execute?sandbox=true
 * - Real-time step timeline showing status per step
 */

import { useCallback, useRef, useState } from 'react';
import {
  Badge,
  Button,
  Card,
  Group,
  Loader,
  Stack,
  Text,
  Timeline,
  Title,
} from '@mantine/core';
import { useAuthStore } from '../../state/authStore';

/* eslint-disable @typescript-eslint/no-explicit-any */

interface StepEvent {
  step?: number;
  total_steps?: number;
  skill?: string;
  status: string;
  message?: string;
  result?: any;
}

interface WorkflowTesterProps {
  workflowId: string | null;
}

type TesterStatus = 'idle' | 'running' | 'done' | 'error';

function statusColor(s: string): string {
  switch (s) {
    case 'done':
    case 'completed':
      return 'green';
    case 'running':
      return 'blue';
    case 'error':
      return 'red';
    case 'awaiting_confirmation':
      return 'yellow';
    default:
      return 'gray';
  }
}

export function WorkflowTester({ workflowId }: WorkflowTesterProps) {
  const [status, setStatus] = useState<TesterStatus>('idle');
  const [events, setEvents] = useState<StepEvent[]>([]);
  const [error, setError] = useState<string | null>(null);
  const abortRef = useRef<AbortController | null>(null);

  const runTest = useCallback(async () => {
    if (!workflowId) return;

    abortRef.current?.abort();
    const controller = new AbortController();
    abortRef.current = controller;

    setStatus('running');
    setEvents([]);
    setError(null);

    const token = useAuthStore.getState().token;
    const url =
      `/api/workflows/${workflowId}/execute` +
      `?sandbox=true&token=${encodeURIComponent(token || '')}`;

    try {
      const response = await fetch(url, {
        method: 'POST',
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
          const lines = part.split('\n');
          for (const line of lines) {
            const trimmed = line.trim();
            if (!trimmed.startsWith('data: ')) continue;
            try {
              const data = JSON.parse(trimmed.slice(6)) as StepEvent;
              setEvents((prev) => [...prev, data]);
              if (data.status === 'completed' || data.status === 'error') {
                setStatus(data.status === 'completed' ? 'done' : 'error');
              }
            } catch {
              /* skip malformed */
            }
          }
        }
      }

      setStatus((prev) => (prev === 'running' ? 'done' : prev));
    } catch (err: unknown) {
      if (err instanceof DOMException && err.name === 'AbortError') return;
      setError('Conexão perdida.');
      setStatus('error');
    } finally {
      abortRef.current = null;
    }
  }, [workflowId]);

  const stop = useCallback(() => {
    abortRef.current?.abort();
    abortRef.current = null;
    setStatus('done');
  }, []);

  if (!workflowId) {
    return (
      <Card shadow="xs" padding="md" radius="md" withBorder mt="lg">
        <Text c="dimmed" size="sm">
          Salve o workflow primeiro para poder testá-lo.
        </Text>
      </Card>
    );
  }

  // Filter step-level events (exclude workflow-level started/completed)
  const stepEvents = events.filter((e) => e.step != null);

  return (
    <Card shadow="xs" padding="md" radius="md" withBorder mt="lg">
      <Stack gap="md">
        <Group justify="space-between">
          <Title order={5}>🧪 Testador Sandbox</Title>
          <Group gap="xs">
            {status === 'running' ? (
              <Button
                variant="light"
                color="red"
                size="xs"
                onClick={stop}
              >
                ⏹ Parar
              </Button>
            ) : (
              <Button
                variant="gradient"
                gradient={{ from: 'blue', to: 'cyan', deg: 90 }}
                size="xs"
                onClick={runTest}
              >
                ▶ Testar
              </Button>
            )}
          </Group>
        </Group>

        {/* Error display */}
        {error && (
          <Text c="red" size="sm">
            {error}
          </Text>
        )}

        {/* Timeline of step execution */}
        {stepEvents.length > 0 && (
          <Timeline
            active={
              stepEvents.filter(
                (e) => e.status === 'done' || e.status === 'error',
              ).length - 1
            }
            bulletSize={24}
            lineWidth={2}
          >
            {stepEvents.map((ev, i) => (
              <Timeline.Item
                key={i}
                title={
                  <Group gap="xs">
                    <Text size="sm" fw={500}>
                      Step {ev.step} — {ev.skill}
                    </Text>
                    <Badge
                      size="xs"
                      color={statusColor(ev.status)}
                      variant="light"
                    >
                      {ev.status}
                    </Badge>
                  </Group>
                }
                bullet={
                  ev.status === 'running' ? (
                    <Loader size={12} color="blue" />
                  ) : undefined
                }
                color={statusColor(ev.status)}
              >
                {ev.message && (
                  <Text size="xs" c="dimmed">
                    {ev.message}
                  </Text>
                )}
                {ev.result && (
                  <Text size="xs" c="dimmed" lineClamp={2}>
                    {JSON.stringify(ev.result).slice(0, 200)}
                  </Text>
                )}
              </Timeline.Item>
            ))}
          </Timeline>
        )}

        {/* Status indicator */}
        {status === 'running' && stepEvents.length === 0 && (
          <Group gap="xs" justify="center" py="sm">
            <Loader size="sm" />
            <Text size="sm" c="dimmed">
              Iniciando execução…
            </Text>
          </Group>
        )}

        {status === 'done' && (
          <Text size="sm" c="green" ta="center">
            ✅ Teste finalizado
          </Text>
        )}
      </Stack>
    </Card>
  );
}
