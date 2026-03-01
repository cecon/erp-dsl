/**
 * WorkflowStepEditor — visual step list editor for workflow definitions.
 *
 * Registered in ComponentRegistry as 'workflow_step_editor'.
 * Receives value/onChange from DynamicForm's useForm (via getInputProps).
 *
 * Features:
 * - Add / remove steps
 * - Reorder with ▲ ▼ buttons
 * - Skill dropdown fetched from GET /api/otto/components
 * - Dynamic params form generated from the skill's params_schema
 * - Confirmation toggle and on_error policy select per step
 */

import { useCallback } from 'react';
import {
  ActionIcon,
  Badge,
  Button,
  Card,
  Checkbox,
  Group,
  Select,
  Stack,
  Text,
  TextInput,
  Title,
} from '@mantine/core';
import { useSkills, type SkillInfo } from './useSkills';

/* eslint-disable @typescript-eslint/no-explicit-any */

export interface WorkflowStepData {
  skill: string;
  params: Record<string, any>;
  requires_confirmation: boolean;
  on_error: 'stop' | 'continue' | 'ask';
}

interface WorkflowStepEditorProps {
  value?: WorkflowStepData[];
  onChange?: (steps: WorkflowStepData[]) => void;
  label?: string;
}

const EMPTY_STEP: WorkflowStepData = {
  skill: '',
  params: {},
  requires_confirmation: false,
  on_error: 'stop',
};

const ON_ERROR_OPTIONS = [
  { value: 'stop', label: '⛔ Parar' },
  { value: 'continue', label: '⏭️ Continuar' },
  { value: 'ask', label: '❓ Perguntar' },
];

/**
 * Render dynamic param fields based on a skill's params_schema.
 */
function ParamsFields({
  schema,
  params,
  onParamChange,
}: {
  schema: SkillInfo['params_schema'];
  params: Record<string, any>;
  onParamChange: (key: string, value: any) => void;
}) {
  if (!schema?.properties) return null;

  return (
    <Stack gap="xs">
      {Object.entries(schema.properties).map(([key, prop]) => {
        if (prop.enum) {
          return (
            <Select
              key={key}
              label={prop.description || key}
              placeholder={`Selecione ${key}`}
              data={prop.enum.map((v) => ({ value: v, label: v }))}
              value={params[key] ?? null}
              onChange={(val) => onParamChange(key, val)}
              size="xs"
              clearable
            />
          );
        }
        return (
          <TextInput
            key={key}
            label={prop.description || key}
            placeholder={key}
            value={params[key] ?? ''}
            onChange={(e) => onParamChange(key, e.currentTarget.value)}
            size="xs"
          />
        );
      })}
    </Stack>
  );
}

export function WorkflowStepEditor({
  value = [],
  onChange,
  label,
}: WorkflowStepEditorProps) {
  const { skills, isLoading: skillsLoading } = useSkills();
  const steps = Array.isArray(value) ? value : [];

  const skillOptions = skills.map((s) => ({
    value: s.name,
    label: `${s.name} — ${s.description}`,
  }));

  const getSkillSchema = useCallback(
    (skillName: string): SkillInfo['params_schema'] => {
      return skills.find((s) => s.name === skillName)?.params_schema;
    },
    [skills],
  );

  // ── Mutators ──────────────────────────────────────────────

  const updateSteps = useCallback(
    (newSteps: WorkflowStepData[]) => onChange?.(newSteps),
    [onChange],
  );

  const addStep = useCallback(() => {
    updateSteps([...steps, { ...EMPTY_STEP }]);
  }, [steps, updateSteps]);

  const removeStep = useCallback(
    (idx: number) => {
      updateSteps(steps.filter((_, i) => i !== idx));
    },
    [steps, updateSteps],
  );

  const moveStep = useCallback(
    (idx: number, direction: -1 | 1) => {
      const target = idx + direction;
      if (target < 0 || target >= steps.length) return;
      const copy = [...steps];
      [copy[idx], copy[target]] = [copy[target], copy[idx]];
      updateSteps(copy);
    },
    [steps, updateSteps],
  );

  const updateStep = useCallback(
    (idx: number, patch: Partial<WorkflowStepData>) => {
      const copy = [...steps];
      copy[idx] = { ...copy[idx], ...patch };
      updateSteps(copy);
    },
    [steps, updateSteps],
  );

  const updateParam = useCallback(
    (idx: number, key: string, val: any) => {
      const copy = [...steps];
      copy[idx] = {
        ...copy[idx],
        params: { ...copy[idx].params, [key]: val },
      };
      updateSteps(copy);
    },
    [steps, updateSteps],
  );

  // ── Render ────────────────────────────────────────────────

  return (
    <Stack gap="md">
      {label && (
        <Title order={5} c="dimmed">
          {label}
        </Title>
      )}

      {steps.length === 0 && (
        <Text c="dimmed" size="sm" ta="center" py="md">
          Nenhum step adicionado. Clique em "Adicionar Step" abaixo.
        </Text>
      )}

      {steps.map((step, idx) => (
        <Card
          key={idx}
          shadow="xs"
          padding="md"
          radius="md"
          withBorder
          style={{ borderLeft: '3px solid var(--mantine-color-blue-6)' }}
        >
          {/* Header: step number + move + remove */}
          <Group justify="space-between" mb="sm">
            <Group gap="xs">
              <Badge variant="filled" size="sm" radius="xl">
                {idx + 1}
              </Badge>
              <Text size="sm" fw={600}>
                {step.skill || 'Selecione uma skill'}
              </Text>
            </Group>
            <Group gap={4}>
              <ActionIcon
                variant="subtle"
                size="sm"
                disabled={idx === 0}
                onClick={() => moveStep(idx, -1)}
                title="Mover para cima"
              >
                ▲
              </ActionIcon>
              <ActionIcon
                variant="subtle"
                size="sm"
                disabled={idx === steps.length - 1}
                onClick={() => moveStep(idx, 1)}
                title="Mover para baixo"
              >
                ▼
              </ActionIcon>
              <ActionIcon
                variant="subtle"
                color="red"
                size="sm"
                onClick={() => removeStep(idx)}
                title="Remover step"
              >
                ✕
              </ActionIcon>
            </Group>
          </Group>

          <Stack gap="sm">
            {/* Skill selector */}
            <Select
              label="Skill"
              placeholder={
                skillsLoading ? 'Carregando skills…' : 'Selecione a skill'
              }
              data={skillOptions}
              value={step.skill || null}
              onChange={(val) =>
                updateStep(idx, { skill: val ?? '', params: {} })
              }
              searchable
              clearable
            />

            {/* Dynamic params from params_schema */}
            {step.skill && (
              <ParamsFields
                schema={getSkillSchema(step.skill)}
                params={step.params}
                onParamChange={(k, v) => updateParam(idx, k, v)}
              />
            )}

            {/* Confirmation + on_error */}
            <Group gap="lg">
              <Checkbox
                label="Requer confirmação humana"
                checked={step.requires_confirmation}
                onChange={(e) =>
                  updateStep(idx, {
                    requires_confirmation: e.currentTarget.checked,
                  })
                }
              />
              <Select
                label="Em caso de erro"
                data={ON_ERROR_OPTIONS}
                value={step.on_error}
                onChange={(val) =>
                  updateStep(idx, {
                    on_error: (val as WorkflowStepData['on_error']) || 'stop',
                  })
                }
                size="xs"
                w={180}
              />
            </Group>
          </Stack>
        </Card>
      ))}

      <Button variant="light" onClick={addStep} fullWidth>
        + Adicionar Step
      </Button>
    </Stack>
  );
}
