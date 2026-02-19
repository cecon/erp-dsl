import { ColorSwatch, Group, Text, Tooltip } from '@mantine/core';

/* eslint-disable @typescript-eslint/no-explicit-any */

interface ColorSwatchPickerProps {
  label?: string;
  value?: string;
  onChange?: (value: string) => void;
  options?: { value: string; hex: string }[];
}

/**
 * DSL component: renders a row of color swatches.
 * Schema options provide `value` (Mantine color name) and `hex` for display.
 */
export function ColorSwatchPicker({
  label,
  value,
  onChange,
  options = [],
}: ColorSwatchPickerProps) {
  return (
    <div>
      {label && <Text size="sm" fw={600} mb="xs">{label}</Text>}
      <Group gap="xs">
        {options.map((opt: any) => (
          <Tooltip label={opt.value} key={opt.value}>
            <ColorSwatch
              color={opt.hex}
              onClick={() => onChange?.(opt.value)}
              style={{
                cursor: 'pointer',
                outline: value === opt.value
                  ? `2px solid ${opt.hex}`
                  : '2px solid transparent',
                outlineOffset: 2,
              }}
            />
          </Tooltip>
        ))}
      </Group>
    </div>
  );
}
