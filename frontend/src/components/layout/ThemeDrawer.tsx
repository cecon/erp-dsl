import {
  Divider,
  Drawer,
  Stack,
  Text,
  useMantineColorScheme,
} from '@mantine/core';
import { useQuery } from '@tanstack/react-query';
import api from '../../services/api';
import { getComponent } from '../../core/engine/ComponentRegistry';
import { useThemeStore } from '../../state/themeStore';

/* eslint-disable @typescript-eslint/no-explicit-any */

/**
 * DSL-driven Theme Drawer.
 *
 * Fetches the _theme_config schema from the API and renders each
 * component dynamically using the ComponentRegistry. No hardcoded
 * controls — everything comes from the DSL schema.
 *
 * The drawer open/close state is managed by themeStore (Zustand),
 * allowing the Header to trigger it via openThemeDrawer().
 */
export function ThemeDrawer() {
  const opened = useThemeStore((s) => s.themeDrawerOpened);
  const close = useThemeStore((s) => s.closeThemeDrawer);

  // Individual selectors to avoid subscribing to the entire store
  const primaryColor = useThemeStore((s) => s.primaryColor);
  const colorScheme = useThemeStore((s) => s.colorScheme);
  const radius = useThemeStore((s) => s.radius);
  const fontSize = useThemeStore((s) => s.fontSize);
  const sidebarCollapsed = useThemeStore((s) => s.sidebarCollapsed);
  const setPrimaryColor = useThemeStore((s) => s.setPrimaryColor);
  const setColorScheme = useThemeStore((s) => s.setColorScheme);
  const setRadius = useThemeStore((s) => s.setRadius);
  const setFontSize = useThemeStore((s) => s.setFontSize);
  const toggleSidebar = useThemeStore((s) => s.toggleSidebar);

  const { setColorScheme: setMantineScheme } = useMantineColorScheme();

  const { data } = useQuery({
    queryKey: ['page', '_theme_config'],
    queryFn: () => api.get('/pages/_theme_config').then((r) => r.data),
  });

  const getValue = (id: string): any => {
    const map: Record<string, any> = {
      primaryColor,
      colorScheme,
      radius,
      fontSize,
      sidebarCollapsed,
    };
    return map[id];
  };

  const handleChange = (id: string, value: any) => {
    const handlers: Record<string, (v: any) => void> = {
      primaryColor: (v) => setPrimaryColor(v),
      colorScheme: (v) => {
        setColorScheme(v);
        setMantineScheme(v);
      },
      radius: (v) => setRadius(v),
      fontSize: (v) => setFontSize(v),
      sidebarCollapsed: () => toggleSidebar(),
    };
    handlers[id]?.(value);
  };

  const schema = data?.schema;
  const components = schema?.components ?? [];

  return (
    <Drawer
      opened={opened}
      onClose={close}
      title={data?.schema?.title ?? 'Theme Settings'}
      position="right"
      size="xs"
      overlayProps={{ backgroundOpacity: 0.4, blur: 2 }}
    >
      <Stack gap="lg">
        {components.map((comp: any, idx: number) => {
          const Component = getComponent(comp.type);
          if (!Component) {
            return (
              <Text key={comp.id} c="red" size="sm">
                Unknown type: {comp.type}
              </Text>
            );
          }

          return (
            <div key={comp.id}>
              <Component
                label={comp.label}
                value={getValue(comp.id)}
                onChange={(v: any) => handleChange(comp.id, v)}
                options={comp.options}
                on_label={comp.on_label}
                off_label={comp.off_label}
                on_value={comp.on_value}
                off_value={comp.off_value}
              />
              {idx < components.length - 1 && <Divider mt="lg" />}
            </div>
          );
        })}
      </Stack>
    </Drawer>
  );
}
