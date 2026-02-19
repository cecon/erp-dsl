import { Select, type SelectProps } from '@mantine/core';

export interface SelectFieldProps extends Omit<SelectProps, 'onChange' | 'data'> {
  value?: string | null;
  onChange?: (value: string | null) => void;
  options?: { value: string; label: string }[];
}

/**
 * Select/dropdown field for the DSL engine.
 * Maps the DSL `options` prop to Mantine's `data` prop automatically.
 */
export function SelectField({ value, onChange, options, ...rest }: SelectFieldProps) {
  return (
    <Select
      value={value ?? null}
      onChange={(val) => onChange?.(val)}
      data={options ?? []}
      clearable
      searchable
      {...rest}
    />
  );
}
