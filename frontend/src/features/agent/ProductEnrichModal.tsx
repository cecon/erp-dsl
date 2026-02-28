/**
 * ProductEnrichModal — AI-powered product enrichment modal.
 *
 * Registered in ComponentRegistry as 'agent:product-enrich'.
 * Consumes SSE via useProductEnrich and displays a Mantine Timeline
 * with real-time agent steps, draft preview, and a save button.
 */

import {
  Badge,
  Button,
  Group,
  Loader,
  Modal,
  SimpleGrid,
  Stack,
  Text,
  TextInput,
  Timeline,
} from '@mantine/core';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { useCallback, useState } from 'react';
import api from '../../services/api';
import { type AgentStep, useProductEnrich } from './useProductEnrich';

/* eslint-disable @typescript-eslint/no-explicit-any */

/* ── Props ────────────────────────────────────────────────────────── */

interface ProductEnrichModalProps {
  opened: boolean;
  onClose: () => void;
  /** The entity endpoint to POST the saved product to */
  endpoint?: string;
  /** react-query key to invalidate after saving */
  queryKey?: string;
}

/* ── Step icon / label helpers ────────────────────────────────────── */

function stepIcon(step: AgentStep): string {
  if (step.done && !step.error) return '✅';
  if (step.done && step.error) return '❌';
  if (step.skill === 'fetch_by_ean') return '🔍';
  if (step.skill === 'classify_ncm') return '🗂️';
  return '⚙️';
}

function stepTitle(step: AgentStep): string {
  if (step.done && !step.error) return 'Enriquecimento concluído';
  if (step.done && step.error) return `Erro: ${step.error}`;
  if (step.skill === 'fetch_by_ean') return 'Buscando dados pelo EAN…';
  if (step.skill === 'classify_ncm') return 'Classificando NCM…';
  if (step.step === 'skill_call') return `Executando ${step.skill ?? 'skill'}…`;
  if (step.step === 'parse_error') return 'Corrigindo resposta da IA…';
  return `Step ${step.iteration}`;
}

function stepColor(step: AgentStep): string {
  if (step.done && !step.error) return 'teal';
  if (step.done && step.error) return 'red';
  return 'blue';
}

/* ── Component ────────────────────────────────────────────────────── */

export function ProductEnrichModal({
  opened,
  onClose,
  endpoint = '/entities/products',
  queryKey = 'products',
}: ProductEnrichModalProps) {
  const [input, setInput] = useState('');
  const { status, steps, draft, error, start, reset } = useProductEnrich();
  const queryClient = useQueryClient();

  const saveMutation = useMutation({
    mutationFn: (values: any) => api.post(endpoint, values),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [queryKey] });
      handleClose();
    },
  });

  const handleStart = useCallback(() => {
    if (!input.trim()) return;
    start(input.trim());
  }, [input, start]);

  const handleClose = useCallback(() => {
    reset();
    setInput('');
    onClose();
  }, [reset, onClose]);

  const handleSave = useCallback(() => {
    if (!draft) return;
    saveMutation.mutate(draft);
  }, [draft, saveMutation]);

  return (
    <Modal
      opened={opened}
      onClose={handleClose}
      title="Novo Produto com IA"
      centered
      size="lg"
      overlayProps={{ backgroundOpacity: 0.6, blur: 3 }}
    >
      <Stack gap="md">
        {/* ── Input ──────────────────────────────────────────── */}
        <TextInput
          label="EAN ou descrição do produto"
          placeholder="Ex: 7891234567890 ou 'Café torrado 500g'"
          value={input}
          onChange={(e) => setInput(e.currentTarget.value)}
          disabled={status === 'streaming'}
          onKeyDown={(e) => {
            if (e.key === 'Enter') handleStart();
          }}
        />

        <Button
          onClick={handleStart}
          loading={status === 'streaming'}
          disabled={!input.trim() || status === 'streaming'}
          variant="gradient"
          gradient={{ from: 'blue', to: 'cyan', deg: 90 }}
          fullWidth
        >
          ✨ Enriquecer com IA
        </Button>

        {/* ── Timeline ──────────────────────────────────────── */}
        {steps.length > 0 && (
          <div className="agent-timeline-wrapper">
            <Timeline
              active={steps.length - 1}
              bulletSize={28}
              lineWidth={2}
              color="blue"
            >
              {steps.map((step, idx) => (
                <Timeline.Item
                  key={idx}
                  bullet={<span style={{ fontSize: 14 }}>{stepIcon(step)}</span>}
                  title={
                    <Text size="sm" fw={600}>
                      {stepTitle(step)}
                    </Text>
                  }
                  color={stepColor(step)}
                >
                  {step.result && (
                    <Text size="xs" c="dimmed" mt={4} lineClamp={2}>
                      {JSON.stringify(step.result).substring(0, 120)}…
                    </Text>
                  )}
                </Timeline.Item>
              ))}
            </Timeline>

            {status === 'streaming' && (
              <Group gap="xs" mt="sm">
                <Loader size="xs" />
                <Text size="xs" c="dimmed">
                  Processando…
                </Text>
              </Group>
            )}
          </div>
        )}

        {/* ── Error ─────────────────────────────────────────── */}
        {status === 'error' && error && (
          <div className="agent-error-banner">
            <Text size="sm" c="red">
              {error}
            </Text>
            <Button size="xs" variant="subtle" color="red" onClick={reset}>
              Tentar novamente
            </Button>
          </div>
        )}

        {/* ── Draft Preview ─────────────────────────────────── */}
        {status === 'done' && draft && (
          <div className="agent-draft-preview">
            <Text size="sm" fw={700} mb="sm">
              📋 Dados enriquecidos
            </Text>
            <SimpleGrid cols={2} spacing="xs">
              {Object.entries(draft).map(([key, value]) => (
                <div key={key} className="agent-draft-field">
                  <Text size="xs" c="dimmed" tt="uppercase" fw={600}>
                    {key.replace(/_/g, ' ')}
                  </Text>
                  <Text size="sm">
                    {value != null ? String(value) : '—'}
                  </Text>
                </div>
              ))}
            </SimpleGrid>

            <Group justify="flex-end" mt="md" gap="sm">
              <Badge color="teal" variant="light" size="lg">
                Pronto para salvar
              </Badge>
              <Button
                onClick={handleSave}
                loading={saveMutation.isPending}
                variant="gradient"
                gradient={{ from: 'teal', to: 'green', deg: 90 }}
              >
                💾 Salvar Produto
              </Button>
            </Group>
          </div>
        )}
      </Stack>
    </Modal>
  );
}
