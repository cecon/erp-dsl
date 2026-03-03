import { useEffect, useRef } from 'react';
import { Alert, Button, Divider, Group, Stack, Title } from '@mantine/core';
import { useForm } from '@mantine/form';
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

export interface SchemaField {
  id: string;
  type: string;
  label?: string;
  placeholder?: string;
  options?: { value: string; label: string }[];
  condition?: FieldCondition;
  components?: SchemaField[]; // for type === 'section'
  readonly?: boolean;
  computed?: ComputedDef;
  dataSource?: string;
}

interface DynamicFormProps {
  fields: SchemaField[];
  initialValues?: Record<string, any>;
  onSubmit: (values: Record<string, any>) => void;
  onCancel?: () => void;
  submitLabel?: string;
}

/**
 * Flatten all field IDs from a nested schema (including inside sections)
 * into a flat Record for use as form initialValues.
 */
function flattenFieldIds(
  fields: SchemaField[],
  existing: Record<string, any>,
): Record<string, any> {
  const result: Record<string, any> = {};
  for (const field of fields) {
    if (field.type === 'section' && field.components) {
      // Recurse into section children — they are first-level form values
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
    if (field.type === 'section' && field.components) {
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
 * - Conditional visibility via `condition: { field, value }`
 * - Readonly computed fields (e.g. markup, margem)
 *
 * Section children are treated as first-level form values (flattened),
 * NOT nested under a section key.
 */
export function DynamicForm({
  fields,
  initialValues = {},
  onSubmit,
  onCancel,
  submitLabel = 'Save',
}: DynamicFormProps) {
  const form = useForm({
    initialValues: flattenFieldIds(fields, initialValues),
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
      return (
        <div key={field.id}>
          <Divider my="md" />
          <Title order={5} mb="sm">
            {field.label}
          </Title>
          <Stack gap="md">
            {field.components?.map((child) => renderField(child))}
          </Stack>
        </div>
      );
    }

    // Regular field
    const Component = getComponent(field.type);
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

    return (
      <Component
        key={field.id}
        label={field.label}
        placeholder={field.placeholder || field.label}
        options={field.options}
        readOnly={field.readonly}
        disabled={field.readonly}
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
