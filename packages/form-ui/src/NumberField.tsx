import { NumberInput } from '@mantine/core';
import { useState } from 'react';
import { FieldWrapper, type FieldWrapperProps } from './FieldWrapper';

export interface NumberFieldProps
  extends Omit<FieldWrapperProps, 'children' | 'currentLength' | 'touched' | 'hasValue' | 'maxLength'> {
  value?: number | string;
  onChange?: (value: number | string) => void;
  placeholder?: string;
  readOnly?: boolean;
  disabled?: boolean;
  min?: number;
  max?: number;
  error?: string;
}

/**
 * Numeric input field for the DSL engine.
 * Wraps Mantine NumberInput com separadores BR + badge + ícone de status.
 */
export function NumberField({
  value,
  onChange,
  placeholder,
  readOnly,
  disabled,
  label,
  required,
  description,
  error,
  min,
  max,
}: NumberFieldProps) {
  const [touched, setTouched] = useState(false);

  const hasValue = value !== '' && value !== undefined && value !== null;

  return (
    <FieldWrapper
      label={label}
      required={required}
      description={description}
      error={error}
      touched={touched}
      hasValue={!!hasValue}
    >
      <NumberInput
        value={value ?? ''}
        onChange={(val) => onChange?.(val)}
        onBlur={() => setTouched(true)}
        placeholder={placeholder}
        readOnly={readOnly}
        disabled={disabled}
        allowNegative={false}
        thousandSeparator="."
        decimalSeparator=","
        min={min}
        max={max}
        error={!!error}
        aria-invalid={!!error}
      />
    </FieldWrapper>
  );
}
