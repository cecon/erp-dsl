import { NumberInput, type NumberInputProps } from '@mantine/core';

export interface MoneyFieldProps extends Omit<NumberInputProps, 'onChange'> {
  value?: number | string;
  onChange?: (value: number | string) => void;
}

/**
 * Currency input field for the DSL engine.
 * Pre-configured for BRL: R$ prefix, 2 decimal places, BR separators.
 */
export function MoneyField({ value, onChange, ...rest }: MoneyFieldProps) {
  return (
    <NumberInput
      value={value ?? ''}
      onChange={(val) => onChange?.(val)}
      prefix="R$ "
      decimalScale={2}
      fixedDecimalScale
      thousandSeparator="."
      decimalSeparator=","
      allowNegative={false}
      min={0}
      {...rest}
    />
  );
}
