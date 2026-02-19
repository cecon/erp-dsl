import {
  ActionIcon,
  Divider,
  Drawer,
  Stack,
  Text,
  Tooltip,
  useMantineColorScheme,
} from '@mantine/core';
import { useDisclosure } from '@mantine/hooks';
import { useQuery } from '@tanstack/react-query';
import api from '../../services/api';
import { getComponent } from '../engine/ComponentRegistry';
import { useThemeStore } from '../../state/themeStore';

/* eslint-disable @typescript-eslint/no-explicit-any */

/**
 * DSL-driven Theme Drawer.
 *
 * Fetches the _theme_config schema from the API and renders each
 * component dynamically using the ComponentRegistry. No hardcoded
 * controls — everything comes from the DSL schema.
 */
export function ThemeDrawer() {
  const [opened, { open, close }] = useDisclosure(false);
  const themeStore = useThemeStore();
  const { setColorScheme: setMantineScheme } = useMantineColorScheme();

  const { data } = useQuery({
    queryKey: ['page', '_theme_config'],
    queryFn: () => api.get('/pages/_theme_config').then((r) => r.data),
  });

  /**
   * Resolves the current value for each DSL component by id,
   * reading from the Zustand theme store.
   */
  const getValue = (id: string): any => {
    const map: Record<string, any> = {
      primaryColor: themeStore.primaryColor,
      colorScheme: themeStore.colorScheme,
      radius: themeStore.radius,
      fontSize: themeStore.fontSize,
      sidebarCollapsed: themeStore.sidebarCollapsed,
    };
    return map[id];
  };

  /**
   * Dispatches value changes to the correct themeStore setter.
   * Handles special cases like colorScheme that also needs
   * to sync with Mantine's internal scheme.
   */
  const handleChange = (id: string, value: any) => {
    const handlers: Record<string, (v: any) => void> = {
      primaryColor: (v) => themeStore.setPrimaryColor(v),
      colorScheme: (v) => {
        themeStore.setColorScheme(v);
        setMantineScheme(v);
      },
      radius: (v) => themeStore.setRadius(v),
      fontSize: (v) => themeStore.setFontSize(v),
      sidebarCollapsed: () => themeStore.toggleSidebar(),
    };
    handlers[id]?.(value);
  };

  const schema = data?.schema;
  const components = schema?.components ?? [];

  return (
    <>
      <Tooltip label="Theme Settings" position="left">
        <ActionIcon
          className="theme-gear-btn"
          variant="filled"
          size="lg"
          radius="xl"
          onClick={open}
          aria-label="Open theme settings"
        >
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <circle cx="12" cy="12" r="3" />
            <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z" />
          </svg>
        </ActionIcon>
      </Tooltip>

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
    </>
  );
}
