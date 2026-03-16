import { NumberInput } from '@mantine/core';
import { useState } from 'react';
import { FieldWrapper, type FieldWrapperProps } from './FieldWrapper';

export interface MoneyFieldProps
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
 * Currency input field for the DSL engine.
 * Pre-configured for BRL: R$ prefix, 2 decimal places, BR separators.
 * Inclui badge Obrigatório/Opcional e ícone de status via FieldWrapper.
 */
export function MoneyField({
  value,
  onChange,
  placeholder,
  readOnly,
  disabled,
  label,
  required,
  description,
  error,
  min = 0,
  max,
}: MoneyFieldProps) {
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
        prefix="R$ "
        decimalScale={2}
        fixedDecimalScale
        thousandSeparator="."
        decimalSeparator=","
        allowNegative={false}
        min={min}
        max={max}
        error={!!error}
        aria-invalid={!!error}
      />
    </FieldWrapper>
  );
}
