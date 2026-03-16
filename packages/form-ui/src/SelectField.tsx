import { Select } from '@mantine/core';
import axios from 'axios';
import { useEffect, useState } from 'react';
import { FieldWrapper, type FieldWrapperProps } from './FieldWrapper';

export interface SelectFieldProps
  extends Omit<FieldWrapperProps, 'children' | 'currentLength' | 'touched' | 'hasValue' | 'maxLength'> {
  value?: string | null;
  onChange?: (value: string | null) => void;
  options?: { value: string; label: string }[];
  /** URL to fetch options from (e.g. "/api/llm/models") */
  dataSource?: string;
  /** Query params to append to the dataSource URL */
  dataSourceParams?: Record<string, string>;
  placeholder?: string;
  readOnly?: boolean;
  disabled?: boolean;
  error?: string;
}

/**
 * Select/dropdown field for the DSL engine.
 * Maps the DSL `options` prop to Mantine's `data` prop automatically.
 *
 * When `dataSource` is provided, options are fetched from the endpoint
 * dynamically. The `dataSourceParams` are appended as query params.
 * Inclui badge Obrigatório/Opcional e ícone de status via FieldWrapper.
 */
export function SelectField({
  value,
  onChange,
  options,
  dataSource,
  dataSourceParams,
  placeholder,
  readOnly,
  disabled,
  label,
  required,
  description,
  error,
}: SelectFieldProps) {
  const [dynamicOptions, setDynamicOptions] = useState<
    { value: string; label: string }[] | null
  >(null);
  const [loading, setLoading] = useState(false);
  const [touched, setTouched] = useState(false);

  // Serialize params to use as dependency
  const paramsKey = dataSourceParams ? JSON.stringify(dataSourceParams) : '';

  useEffect(() => {
    if (!dataSource || !dataSourceParams) return;

    // Don't fetch if required params are empty
    const hasValues = Object.values(dataSourceParams).some(
      (v) => v && v.trim().length > 0,
    );
    if (!hasValues) return;

    let cancelled = false;
    setLoading(true);

    const url = dataSource.startsWith('/api') ? dataSource : `/api${dataSource}`;

    axios
      .get(url, { params: dataSourceParams })
      .then((res) => {
        if (!cancelled && Array.isArray(res.data)) {
          setDynamicOptions(res.data);
        }
      })
      .catch(() => {
        if (!cancelled) setDynamicOptions(null);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [dataSource, paramsKey]);

  const finalOptions = dynamicOptions ?? options ?? [];
  const hasValue = value !== null && value !== undefined && value !== '';

  return (
    <FieldWrapper
      label={label}
      required={required}
      description={description}
      error={error}
      touched={touched}
      hasValue={hasValue}
    >
      <Select
        value={value ?? null}
        onChange={(val) => {
          setTouched(true);
          onChange?.(val);
        }}
        onBlur={() => setTouched(true)}
        data={finalOptions}
        placeholder={loading ? 'Carregando...' : placeholder}
        readOnly={readOnly}
        disabled={disabled}
        clearable
        searchable
        error={!!error}
        aria-invalid={!!error}
      />
    </FieldWrapper>
  );
}
