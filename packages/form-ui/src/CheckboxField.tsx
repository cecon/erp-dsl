import { Checkbox, Text } from '@mantine/core';
import { useState } from 'react';
import { FieldWrapper, type FieldWrapperProps } from './FieldWrapper';

export interface CheckboxFieldProps
  extends Omit<FieldWrapperProps, 'children' | 'currentLength' | 'touched' | 'hasValue' | 'maxLength' | 'label'> {
  value?: boolean;
  onChange?: (value: boolean) => void;
  label?: string;
  disabled?: boolean;
  error?: string;
}

/**
 * Checkbox field for the DSL engine.
 * Normalizes the onChange to emit a boolean value directly.
 * Inclui badge Obrigatório/Opcional e mensagens de erro via FieldWrapper.
 */
export function CheckboxField({
  value,
  onChange,
  label,
  disabled,
  required,
  description,
  error,
}: CheckboxFieldProps) {
  const [touched, setTouched] = useState(false);

  return (
    <FieldWrapper
      required={required}
      description={description}
      error={error}
      touched={touched}
      hasValue={!!value}
    >
      <Checkbox
        checked={!!value}
        onChange={(e) => {
          setTouched(true);
          onChange?.(e.currentTarget.checked);
        }}
        onBlur={() => setTouched(true)}
        disabled={disabled}
        error={!!error}
        label={
          <Text size="sm" fw={500}>
            {label}
            {required && (
              <Text component="span" c="red" ml={2} aria-hidden="true">
                *
              </Text>
            )}
          </Text>
        }
      />
    </FieldWrapper>
  );
}
