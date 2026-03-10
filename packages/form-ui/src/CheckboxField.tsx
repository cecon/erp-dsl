import { Checkbox } from '@mantine/core';

export interface CheckboxFieldProps {
  value?: boolean;
  onChange?: (value: boolean) => void;
  label?: string;
  disabled?: boolean;
  description?: string;
}

/**
 * Checkbox field for the DSL engine.
 * Normalizes the onChange to emit a boolean value directly.
 */
export function CheckboxField({ value, onChange, label, ...rest }: CheckboxFieldProps) {
  return (
    <Checkbox
      checked={!!value}
      onChange={(e) => onChange?.(e.currentTarget.checked)}
      label={label}
      {...rest}
    />
  );
}
