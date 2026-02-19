import { Switch, Text } from '@mantine/core';

interface ThemeSwitchProps {
  label?: string;
  value?: boolean | string;
  onChange?: (value: boolean | string) => void;
  on_label?: string;
  off_label?: string;
  on_value?: string;
  off_value?: string;
}

/**
 * DSL component: boolean or string toggle switch.
 *
 * If on_value/off_value are provided, emits those strings.
 * Otherwise emits boolean true/false.
 */
export function ThemeSwitch({
  label,
  value,
  onChange,
  on_label,
  off_label,
  on_value,
  off_value,
}: ThemeSwitchProps) {
  const isStringMode = on_value !== undefined && off_value !== undefined;
  const checked = isStringMode ? value === on_value : !!value;
  const displayLabel = checked ? (on_label ?? 'On') : (off_label ?? 'Off');

  const handleChange = () => {
    if (isStringMode) {
      onChange?.(checked ? off_value! : on_value!);
    } else {
      onChange?.(!checked);
    }
  };

  return (
    <div>
      {label && <Text size="sm" fw={600} mb="xs">{label}</Text>}
      <Switch
        checked={checked}
        onChange={handleChange}
        label={displayLabel}
        size="md"
      />
    </div>
  );
}
