import { Badge, Group, Stack, Switch, Text } from '@mantine/core';
import { useState } from 'react';
import { FieldWrapper, type FieldWrapperProps } from './FieldWrapper';

export interface SwitchFieldProps
  extends Omit<FieldWrapperProps, 'children' | 'currentLength' | 'touched' | 'hasValue' | 'maxLength' | 'label'> {
  label?: string;
  value?: boolean;
  onChange?: (value: boolean) => void;
  error?: string;
}

/**
 * DSL component: boolean switch toggle for form fields.
 * Renders a Mantine Switch com label, description, badge e ícone de status.
 */
export function SwitchField({
  label,
  description,
  value,
  onChange,
  required,
  error,
}: SwitchFieldProps) {
  const [touched, setTouched] = useState(false);

  return (
    <>
      <Group
        justify="space-between"
        p="sm"
        style={{
          borderRadius: 'var(--mantine-radius-md)',
          border: `1px solid ${error ? 'var(--mantine-color-red-5)' : 'var(--mantine-color-dark-4)'}`,
        }}
      >
        <Stack gap={2}>
          <Group gap={6} align="center">
            <Text fw={600} size="sm">
              {label}
            </Text>
            {required === true && (
              <Badge size="xs" color="red" variant="light" radius="sm">
                Obrigatório
              </Badge>
            )}
            {required === false && (
              <Badge size="xs" color="gray" variant="light" radius="sm">
                Opcional
              </Badge>
            )}
          </Group>
          {description && (
            <Text size="xs" c="dimmed">
              {description}
            </Text>
          )}
        </Stack>
        <Switch
          checked={!!value}
          onChange={(e) => {
            setTouched(true);
            onChange?.(e.currentTarget.checked);
          }}
          onBlur={() => setTouched(true)}
          size="md"
          aria-invalid={!!error}
        />
      </Group>
      {/* FieldWrapper usado apenas para o slot de erro e o ícone de status */}
      <FieldWrapper
        error={error}
        touched={touched}
        hasValue={value === true}
      >
        {/* sem children visíveis — o Switch está acima */}
        <div style={{ display: 'none' }} />
      </FieldWrapper>
    </>
  );
}
