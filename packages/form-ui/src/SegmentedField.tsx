import { SegmentedControl, Stack } from '@mantine/core';
import { FieldWrapper, type FieldWrapperProps } from './FieldWrapper';

export interface SegmentedFieldProps
  extends Omit<FieldWrapperProps, 'children' | 'currentLength' | 'touched' | 'hasValue' | 'maxLength'> {
  value?: string | null;
  onChange?: (value: string | null) => void;
  options?: { value: string; label?: string }[];
  /**
   * Quando true, clicar no segmento já selecionado desmarca a seleção,
   * chamando onChange(null). Útil para filtros opcionais.
   * @default false
   */
  allowDeselect?: boolean;
  error?: string;
}

/**
 * DSL component: wraps Mantine SegmentedControl.
 * Options come from the schema with value + optional label.
 * Supports deselect via allowDeselect prop.
 * Inclui badge Obrigatório/Opcional e ícone de status via FieldWrapper.
 */
export function SegmentedField({
  label,
  value,
  onChange,
  options = [],
  allowDeselect = false,
  required,
  description,
  error,
}: SegmentedFieldProps) {
  const data = options.map((opt) => ({
    value: opt.value,
    label: opt.label ?? opt.value.toUpperCase(),
  }));

  const handleChange = (newValue: string) => {
    if (allowDeselect && newValue === value) {
      onChange?.(null);
    } else {
      onChange?.(newValue);
    }
  };

  const hasValue = value !== null && value !== undefined && value !== '';

  return (
    <FieldWrapper
      label={label}
      required={required}
      description={description}
      error={error}
      // SegmentedControl é sempre "touched" após qualquer interação
      touched={hasValue}
      hasValue={hasValue}
    >
      <Stack gap={0}>
        <SegmentedControl
          value={value ?? ''}
          onChange={handleChange}
          data={data}
          fullWidth
          size="xs"
          style={
            error
              ? { outline: '1px solid var(--mantine-color-red-5)', borderRadius: 'var(--mantine-radius-sm)' }
              : undefined
          }
        />
      </Stack>
    </FieldWrapper>
  );
}
