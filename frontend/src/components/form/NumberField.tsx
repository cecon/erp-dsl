import { NumberInput, type NumberInputProps } from '@mantine/core';

export interface NumberFieldProps extends Omit<NumberInputProps, 'onChange'> {
  value?: number | string;
  onChange?: (value: number | string) => void;
}

/**
 * Numeric input field for the DSL engine.
 * Wraps Mantine NumberInput with project defaults.
 */
export function NumberField({ value, onChange, ...rest }: NumberFieldProps) {
  return (
    <NumberInput
      value={value ?? ''}
      onChange={(val) => onChange?.(val)}
      allowNegative={false}
      thousandSeparator="."
      decimalSeparator=","
      {...rest}
    />
  );
}
