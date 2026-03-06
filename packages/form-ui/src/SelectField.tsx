import { Select, type SelectProps } from '@mantine/core';
import axios from 'axios';
import { useEffect, useState } from 'react';

export interface SelectFieldProps extends Omit<SelectProps, 'onChange' | 'data'> {
  value?: string | null;
  onChange?: (value: string | null) => void;
  options?: { value: string; label: string }[];
  /** URL to fetch options from (e.g. "/api/llm/models") */
  dataSource?: string;
  /** Query params to append to the dataSource URL */
  dataSourceParams?: Record<string, string>;
}

/**
 * Select/dropdown field for the DSL engine.
 * Maps the DSL `options` prop to Mantine's `data` prop automatically.
 *
 * When `dataSource` is provided, options are fetched from the endpoint
 * dynamically. The `dataSourceParams` are appended as query params.
 * Static `options` are used as fallback while loading or if fetch fails.
 */
export function SelectField({
  value,
  onChange,
  options,
  dataSource,
  dataSourceParams,
  ...rest
}: SelectFieldProps) {
  const [dynamicOptions, setDynamicOptions] = useState<
    { value: string; label: string }[] | null
  >(null);
  const [loading, setLoading] = useState(false);

  // Serialize params to use as dependency
  const paramsKey = dataSourceParams
    ? JSON.stringify(dataSourceParams)
    : '';

  useEffect(() => {
    if (!dataSource || !dataSourceParams) return;

    // Don't fetch if required params are empty
    const hasValues = Object.values(dataSourceParams).some(
      (v) => v && v.trim().length > 0,
    );
    if (!hasValues) return;

    let cancelled = false;
    setLoading(true);

    const url = dataSource.startsWith('/api')
      ? dataSource
      : `/api${dataSource}`;

    axios
      .get(url, { params: dataSourceParams })
      .then((res) => {
        if (!cancelled && Array.isArray(res.data)) {
          setDynamicOptions(res.data);
        }
      })
      .catch(() => {
        // Silently fall back to static options
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

  return (
    <Select
      value={value ?? null}
      onChange={(val) => onChange?.(val)}
      data={finalOptions}
      clearable
      searchable
      {...(loading ? { rightSection: undefined, placeholder: 'Carregando modelos...' } : {})}
      {...rest}
    />
  );
}
