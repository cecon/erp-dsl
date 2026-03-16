import { TextInput } from '@mantine/core';
import { useState } from 'react';
import { FieldWrapper, type FieldWrapperProps } from './FieldWrapper';

export interface TextFieldProps
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
 * Standard text input field for the DSL engine.
 * Wraps Mantine TextInput com suporte a char counter, badge
 * Obrigatório/Opcional, ícone de status e helper text via FieldWrapper.
 */
export function TextField({
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
}: TextFieldProps) {
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
      <TextInput
        value={value}
        onChange={(e) => onChange?.(e.currentTarget.value)}
        onBlur={() => setTouched(true)}
        placeholder={placeholder}
        readOnly={readOnly}
        disabled={disabled}
        maxLength={maxLength}
        minLength={minLength}
        error={!!error}
        aria-invalid={!!error}
        styles={{ input: { paddingRight: maxLength ? 8 : undefined } }}
      />
    </FieldWrapper>
  );
}
