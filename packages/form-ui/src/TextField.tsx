import { TextInput, type TextInputProps } from '@mantine/core';

export interface TextFieldProps extends Omit<TextInputProps, 'onChange'> {
  value?: string;
  onChange?: (value: string) => void;
}

/**
 * Standard text input field for the DSL engine.
 * Wraps Mantine TextInput with a simplified onChange signature.
 */
export function TextField({ value, onChange, ...rest }: TextFieldProps) {
  return (
    <TextInput
      value={value ?? ''}
      onChange={(e) => onChange?.(e.currentTarget.value)}
      {...rest}
    />
  );
}
