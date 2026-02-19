import { SegmentedControl, Text } from '@mantine/core';

interface SegmentedFieldProps {
  label?: string;
  value?: string;
  onChange?: (value: string) => void;
  options?: { value: string; label?: string }[];
}

/**
 * DSL component: wraps Mantine SegmentedControl.
 * Options come from the schema with value + optional label.
 */
export function SegmentedField({
  label,
  value,
  onChange,
  options = [],
}: SegmentedFieldProps) {
  const data = options.map((opt) => ({
    value: opt.value,
    label: opt.label ?? opt.value.toUpperCase(),
  }));

  return (
    <div>
      {label && <Text size="sm" fw={600} mb="xs">{label}</Text>}
      <SegmentedControl
        value={value}
        onChange={(v) => onChange?.(v)}
        data={data}
        fullWidth
        size="xs"
      />
    </div>
  );
}
