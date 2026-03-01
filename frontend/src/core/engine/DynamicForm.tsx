import { Alert, Button, Group, Stack } from '@mantine/core';
import { useForm } from '@mantine/form';
import { getComponent } from './ComponentRegistry';

/* eslint-disable @typescript-eslint/no-explicit-any */

interface SchemaField {
  id: string;
  type: string;
  label?: string;
  placeholder?: string;
  options?: { value: string; label: string }[];
}

interface DynamicFormProps {
  fields: SchemaField[];
  initialValues?: Record<string, any>;
  onSubmit: (values: Record<string, any>) => void;
  onCancel?: () => void;
  submitLabel?: string;
}

/**
 * Renders a form dynamically from a DSL schema field list.
 *
 * This component is intentionally free of type-specific logic.
 * All formatting, masks, and defaults are handled by the
 * encapsulated field components resolved via ComponentRegistry.
 */
export function DynamicForm({
  fields,
  initialValues = {},
  onSubmit,
  onCancel,
  submitLabel = 'Save',
}: DynamicFormProps) {
  const form = useForm({
    initialValues: fields.reduce(
      (acc, field) => {
        acc[field.id] = initialValues[field.id] ?? '';
        return acc;
      },
      {} as Record<string, any>
    ),
  });

  return (
    <form onSubmit={form.onSubmit(onSubmit)}>
      <Stack gap="md">
        {fields.map((field) => {
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
              {...form.getInputProps(field.id)}
            />
          );
        })}

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

