import { TextInput } from '@mantine/core';
import { useState } from 'react';
import { FieldWrapper, type FieldWrapperProps } from './FieldWrapper';

export interface DateFieldProps
  extends Omit<FieldWrapperProps, 'children' | 'currentLength' | 'touched' | 'hasValue' | 'maxLength'> {
  value?: string;
  onChange?: (value: string) => void;
  placeholder?: string;
  readOnly?: boolean;
  disabled?: boolean;
  error?: string;
}

/**
 * Date input field for the DSL engine.
 * Uses native HTML date input for broad compatibility.
 * Value format: YYYY-MM-DD (ISO 8601).
 * Inclui badge Obrigatório/Opcional e ícone de status via FieldWrapper.
 */
export function DateField({
  value = '',
  onChange,
  placeholder,
  readOnly,
  disabled,
  label,
  required,
  description,
  error,
}: DateFieldProps) {
  const [touched, setTouched] = useState(false);

  return (
    <FieldWrapper
      label={label}
      required={required}
      description={description}
      error={error}
      touched={touched}
      hasValue={value.length > 0}
    >
      <TextInput
        type="date"
        value={value}
        onChange={(e) => onChange?.(e.currentTarget.value)}
        onBlur={() => setTouched(true)}
        placeholder={placeholder}
        readOnly={readOnly}
        disabled={disabled}
        error={!!error}
        aria-invalid={!!error}
      />
    </FieldWrapper>
  );
}
