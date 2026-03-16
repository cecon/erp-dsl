import { Textarea } from '@mantine/core';
import { useState } from 'react';
import { FieldWrapper, type FieldWrapperProps } from './FieldWrapper';

export interface TextAreaFieldProps
  extends Omit<FieldWrapperProps, 'children' | 'currentLength' | 'touched' | 'hasValue'> {
  value?: string;
  onChange?: (value: string) => void;
  placeholder?: string;
  readOnly?: boolean;
  disabled?: boolean;
  minLength?: number;
  error?: string;
}

/**
 * Multi-line text input field for the DSL engine.
 * Wraps Mantine Textarea com auto-resize + char counter + status UX via FieldWrapper.
 */
export function TextAreaField({
  value = '',
  onChange,
  placeholder,
  readOnly,
  disabled,
  label,
  required,
  maxLength,
  minLength,
  description,
  error,
}: TextAreaFieldProps) {
  const [touched, setTouched] = useState(false);

  return (
    <FieldWrapper
      label={label}
      required={required}
      maxLength={maxLength}
      currentLength={value.length}
      description={description}
      error={error}
      touched={touched}
      hasValue={value.length > 0}
    >
      <Textarea
        value={value}
        onChange={(e) => onChange?.(e.currentTarget.value)}
        onBlur={() => setTouched(true)}
        placeholder={placeholder}
        readOnly={readOnly}
        disabled={disabled}
        maxLength={maxLength}
        minLength={minLength}
        autosize
        minRows={3}
        maxRows={8}
        error={!!error}
        aria-invalid={!!error}
      />
    </FieldWrapper>
  );
}
