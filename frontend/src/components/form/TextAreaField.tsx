import { Textarea, type TextareaProps } from '@mantine/core';

export interface TextAreaFieldProps extends Omit<TextareaProps, 'onChange'> {
  value?: string;
  onChange?: (value: string) => void;
}

/**
 * Multi-line text input field for the DSL engine.
 * Wraps Mantine Textarea with auto-resize enabled.
 */
export function TextAreaField({ value, onChange, ...rest }: TextAreaFieldProps) {
  return (
    <Textarea
      value={value ?? ''}
      onChange={(e) => onChange?.(e.currentTarget.value)}
      autosize
      minRows={3}
      maxRows={8}
      {...rest}
    />
  );
}
