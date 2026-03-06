import { TextInput, type TextInputProps } from '@mantine/core';

export interface DateFieldProps extends Omit<TextInputProps, 'onChange' | 'type'> {
  value?: string;
  onChange?: (value: string) => void;
}

/**
 * Date input field for the DSL engine.
 * Uses native HTML date input for broad compatibility.
 * Value format: YYYY-MM-DD (ISO 8601).
 */
export function DateField({ value, onChange, ...rest }: DateFieldProps) {
  return (
    <TextInput
      type="date"
      value={value ?? ''}
      onChange={(e) => onChange?.(e.currentTarget.value)}
      {...rest}
    />
  );
}
