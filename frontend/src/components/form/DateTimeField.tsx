import { TextInput, type TextInputProps } from '@mantine/core';

export interface DateTimeFieldProps extends Omit<TextInputProps, 'onChange' | 'type'> {
  value?: string;
  onChange?: (value: string) => void;
}

/**
 * Date-time input field for the DSL engine.
 * Uses native HTML datetime-local input for broad compatibility.
 * Value format: YYYY-MM-DDTHH:mm (ISO 8601 local).
 */
export function DateTimeField({ value, onChange, ...rest }: DateTimeFieldProps) {
  return (
    <TextInput
      type="datetime-local"
      value={value ?? ''}
      onChange={(e) => onChange?.(e.currentTarget.value)}
      {...rest}
    />
  );
}
