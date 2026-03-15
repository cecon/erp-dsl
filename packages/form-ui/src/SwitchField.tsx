import { Group, Switch, Text, Stack } from '@mantine/core';

interface SwitchFieldProps {
  label?: string;
  description?: string;
  value?: boolean;
  onChange?: (value: boolean) => void;
  error?: string;
}

/**
 * DSL component: boolean switch toggle for form fields.
 * Renders a Mantine Switch with label and optional description.
 */
export function SwitchField({
  label,
  description,
  value,
  onChange,
}: SwitchFieldProps) {
  return (
    <Group
      justify="space-between"
      p="sm"
      style={{
        borderRadius: 'var(--mantine-radius-md)',
        border: '1px solid var(--mantine-color-dark-4)',
      }}
    >
      <Stack gap={2}>
        <Text fw={600} size="sm">
          {label}
        </Text>
        {description && (
          <Text size="xs" c="dimmed">
            {description}
          </Text>
        )}
      </Stack>
      <Switch
        checked={!!value}
        onChange={(e) => onChange?.(e.currentTarget.checked)}
        size="md"
      />
    </Group>
  );
}
