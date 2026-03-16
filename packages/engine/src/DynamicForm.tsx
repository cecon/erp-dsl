import { Alert, Button, Divider, Group, SimpleGrid, Stack, Tabs, Title } from '@mantine/core';
import { useForm } from '@mantine/form';
import { useEffect, useRef } from 'react';
import { useEngine } from './EngineProvider';
import { getComponent } from './ComponentRegistry';

/* eslint-disable @typescript-eslint/no-explicit-any */

interface FieldCondition {
  field: string;
  value: string;
}

interface ComputedDef {
  formula: string;
  deps: string[];
}

export interface ValidationRule {
  /** Regex como string (será compilado em runtime) */
  pattern?: string;
  /** Mensagem de erro custom para esta regra */
  message?: string;
}

export interface SchemaField {
  id: string;
  type: string;
  label?: string;
  placeholder?: string;
  options?: { value: string; label: string }[];
  condition?: FieldCondition;
  components?: SchemaField[]; // for type === 'section', 'grid', 'tabs' or 'tab'
  columns?: number; // for type === 'grid' (1, 2 or 3)
  readonly?: boolean;
  computed?: ComputedDef;
  dataSource?: string;
  /** Maps form field ids to query param names for dataSource URLs */
  dataSourceParams?: Record<string, string>;
  // ── Validação declarativa ─────────────────────────────────────────────
  /** Campo obrigatório — mostra badge UX e valida no submit */
  required?: boolean;
  /** Limite máximo de caracteres (string) — habilita char counter */
  maxLength?: number;
  /** Mínimo de caracteres (string) */
  minLength?: number;
  /** Valor mínimo permitido (numérico) */
  min?: number;
  /** Valor máximo permitido (numérico) */
  max?: number;
  /** Texto de ajuda exibido abaixo do campo */
  description?: string;
  /** Regras de validação extras (pattern + mensagem custom) */
  validation?: ValidationRule[];
  // ── Deprecação ──────────────────────────────────────────────────────────
  /** Campo marcado para remoção — ativa o DeprecationNotice no FieldWrapper */
  deprecated?: boolean;
  /** Data ISO (YYYY-MM-DD) de remoção: controla a urgência visual */
  deprecatedAt?: string;
  /** Mensagem explicando o motivo e o que o usuário deve fazer */
  deprecationMessage?: string;
}

interface DynamicFormProps {
  fields: SchemaField[];
  initialValues?: Record<string, any>;
  onSubmit: (values: Record<string, any>) => void;
  onCancel?: () => void;
  submitLabel?: string;
}

/** Types that act as layout containers — they recurse into children. */
const CONTAINER_TYPES = new Set(['section', 'grid', 'tabs', 'tab']);

/**
 * Flatten all field IDs from a nested schema (including inside containers)
 * into a flat Record for use as form initialValues.
 */
function flattenFieldIds(
  fields: SchemaField[],
  existing: Record<string, any>,
): Record<string, any> {
  const result: Record<string, any> = {};
  for (const field of fields) {
    if (CONTAINER_TYPES.has(field.type) && field.components) {
      // Recurse into container children — they are first-level form values
      Object.assign(result, flattenFieldIds(field.components, existing));
    } else {
      result[field.id] = existing[field.id] ?? '';
    }
  }
  return result;
}

/**
 * Collect all computed field definitions from the schema tree.
 */
function collectComputed(fields: SchemaField[]): SchemaField[] {
  const result: SchemaField[] = [];
  for (const field of fields) {
    if (CONTAINER_TYPES.has(field.type) && field.components) {
      result.push(...collectComputed(field.components));
    } else if (field.computed) {
      result.push(field);
    }
  }
  return result;
}

/**
 * Built-in formula evaluators for computed fields.
 */
function evalFormula(formula: string, values: Record<string, any>): string {
  const price = parseFloat(values.price) || 0;
  const custo = parseFloat(values.custo) || 0;

  if (formula === 'markup') {
    if (custo <= 0) return '';
    return (((price - custo) / custo) * 100).toFixed(2);
  }
  if (formula === 'margem') {
    if (price <= 0) return '';
    return (((price - custo) / price) * 100).toFixed(2);
  }
  return '';
}

/**
 * Renders a form dynamically from a DSL schema field list.
 *
 * Supports:
 * - Flat fields (text, select, money, textarea, etc.)
 * - Sections (type: "section") with nested child components
 * - Grids (type: "grid") with side-by-side column layout
 * - Tabs (type: "tabs") with tabbed navigation panels
 * - Conditional visibility via `condition: { field, value }`
 * - Readonly computed fields (e.g. markup, margem)
 *
 * Container children are treated as first-level form values (flattened),
 * NOT nested under a container key.
 *
 * Uses the componentRegistry from EngineProvider to resolve field components.
 */
/**
 * Constrói o objeto `validate` do Mantine a partir das regras declarativas
 * do SchemaField, gerando mensagens de erro em PT-BR automaticamente.
 */
function buildValidators(
  fields: SchemaField[],
): Record<string, (value: any) => string | null> {
  const validators: Record<string, (value: any) => string | null> = {};

  function processField(field: SchemaField) {
    if (CONTAINER_TYPES.has(field.type) && field.components) {
      field.components.forEach(processField);
      return;
    }

    const rules: Array<(v: any) => string | null> = [];

    if (field.required) {
      rules.push((v) => {
        if (v === null || v === undefined || v === '' || v === false) {
          return `${field.label ?? field.id} é obrigatório`;
        }
        return null;
      });
    }

    if (field.minLength) {
      const min = field.minLength;
      rules.push((v) =>
        typeof v === 'string' && v.length > 0 && v.length < min
          ? `Mínimo de ${min} caracteres`
          : null,
      );
    }

    if (field.maxLength) {
      const max = field.maxLength;
      rules.push((v) =>
        typeof v === 'string' && v.length > max
          ? `Máximo de ${max} caracteres`
          : null,
      );
    }

    if (field.min !== undefined) {
      const min = field.min;
      rules.push((v) => {
        const n = parseFloat(v);
        return !isNaN(n) && n < min ? `Valor mínimo: ${min}` : null;
      });
    }

    if (field.max !== undefined) {
      const max = field.max;
      rules.push((v) => {
        const n = parseFloat(v);
        return !isNaN(n) && n > max ? `Valor máximo: ${max}` : null;
      });
    }

    if (field.validation) {
      for (const rule of field.validation) {
        if (rule.pattern) {
          const regex = new RegExp(rule.pattern);
          const msg = rule.message ?? `Formato inválido`;
          rules.push((v) =>
            typeof v === 'string' && v.length > 0 && !regex.test(v) ? msg : null,
          );
        }
      }
    }

    if (rules.length > 0) {
      validators[field.id] = (v) => {
        for (const rule of rules) {
          const err = rule(v);
          if (err) return err;
        }
        return null;
      };
    }
  }

  fields.forEach(processField);
  return validators;
}

export function DynamicForm({
  fields,
  initialValues = {},
  onSubmit,
  onCancel,
  submitLabel = 'Save',
}: DynamicFormProps) {
  const { componentRegistry } = useEngine();
  const form = useForm({
    initialValues: flattenFieldIds(fields, initialValues),
    validate: buildValidators(fields),
  });

  // Gather computed fields once
  const computedFields = useRef(collectComputed(fields)).current;

  // Recompute computed fields when their deps change
  useEffect(() => {
    for (const cf of computedFields) {
      if (!cf.computed) continue;
      const newVal = evalFormula(cf.computed.formula, form.values);
      if (form.values[cf.id] !== newVal) {
        form.setFieldValue(cf.id, newVal);
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [
    // Only watch the dependency fields, not all form values
    ...computedFields.flatMap((cf) =>
      (cf.computed?.deps ?? []).map((dep) => form.values[dep]),
    ),
  ]);

  /**
   * Check if a field's condition is met given current form values.
   * If no condition, always visible.
   */
  function isVisible(field: SchemaField): boolean {
    if (!field.condition) return true;
    return form.values[field.condition.field] === field.condition.value;
  }

  /**
   * Render a single field or section recursively.
   */
  function renderField(field: SchemaField) {
    // Check condition — skip rendering if not met
    if (!isVisible(field)) return null;

    // Section: render a titled group with child fields
    if (field.type === 'section') {
      const children = field.components?.map((child) => renderField(child));
      return (
        <div key={field.id}>
          <Divider my="md" />
          <Title order={5} mb="sm">
            {field.label}
          </Title>
          {field.columns ? (
            <SimpleGrid cols={field.columns} spacing="md">
              {children}
            </SimpleGrid>
          ) : (
            <Stack gap="md">
              {children}
            </Stack>
          )}
        </div>
      );
    }

    // Grid: render children side by side in columns
    if (field.type === 'grid') {
      return (
        <SimpleGrid key={field.id} cols={field.columns || 2} spacing="md">
          {field.components?.map((child) => renderField(child))}
        </SimpleGrid>
      );
    }

    // Tabs: render tabbed navigation panels
    if (field.type === 'tabs') {
      const visibleTabs = (field.components ?? []).filter(
        (tab) => tab.type === 'tab' && isVisible(tab),
      );
      if (visibleTabs.length === 0) return null;
      return (
        <Tabs key={field.id} defaultValue={visibleTabs[0]?.id}>
          <Tabs.List mb="md">
            {visibleTabs.map((tab) => (
              <Tabs.Tab key={tab.id} value={tab.id}>
                {tab.label}
              </Tabs.Tab>
            ))}
          </Tabs.List>
          {visibleTabs.map((tab) => (
            <Tabs.Panel key={tab.id} value={tab.id}>
              <Stack gap="md">
                {tab.components?.map((child) => renderField(child))}
              </Stack>
            </Tabs.Panel>
          ))}
        </Tabs>
      );
    }

    // Regular field — resolve from injected registry
    const Component = getComponent(componentRegistry, field.type);
    if (!Component) {
      return (
        <Alert
          key={field.id}
          color="yellow"
          title={`Componente não registrado: ${field.type}`}
          radius="md"
        >
          O tipo de campo <strong>{field.type}</strong> não está disponível
          no ComponentRegistry. Verifique se o componente foi registrado.
        </Alert>
      );
    }

    // Build dynamic options props for selects with dataSource
    const extraProps: Record<string, any> = {};
    if (field.dataSource && field.dataSourceParams) {
      extraProps.dataSource = field.dataSource;
      extraProps.dataSourceParams = {};
      for (const [formField, paramName] of Object.entries(field.dataSourceParams)) {
        extraProps.dataSourceParams[paramName] = form.values[formField] || '';
      }
    }

    // Props de validação/UX a repassar ao componente
    const validationProps: Record<string, any> = {
      required: field.required,
      maxLength: field.maxLength,
      minLength: field.minLength,
      min: field.min,
      max: field.max,
      description: field.description,
      // Deprecação
      deprecated: field.deprecated,
      deprecatedAt: field.deprecatedAt,
      deprecationMessage: field.deprecationMessage,
    };

    return (
      <Component
        key={field.id}
        label={field.label}
        placeholder={field.placeholder || field.label}
        options={field.options}
        readOnly={field.readonly}
        disabled={field.readonly}
        {...validationProps}
        {...extraProps}
        {...form.getInputProps(field.id)}
      />
    );
  }

  return (
    <form onSubmit={form.onSubmit(onSubmit)}>
      <Stack gap="md">
        {fields.map((field) => renderField(field))}

        <Group justify="flex-end" mt="md" gap="sm">
          {onCancel && (
            <Button variant="subtle" color="gray" onClick={onCancel}>
              Cancel
            </Button>
          )}
          <Button type="submit">{submitLabel}</Button>
        </Group>
      </Stack>
    </form>
  );
}
