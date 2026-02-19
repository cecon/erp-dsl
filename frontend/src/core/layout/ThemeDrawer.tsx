import {
  ActionIcon,
  ColorSwatch,
  Divider,
  Drawer,
  Group,
  SegmentedControl,
  Stack,
  Switch,
  Text,
  Tooltip,
  useMantineColorScheme,
} from '@mantine/core';
import { useDisclosure } from '@mantine/hooks';
import { useThemeStore, type PrimaryColor, type RadiusSize } from '../../state/themeStore';

const COLOR_OPTIONS: { color: PrimaryColor; hex: string }[] = [
  { color: 'blue', hex: '#3b82f6' },
  { color: 'teal', hex: '#14b8a6' },
  { color: 'violet', hex: '#8b5cf6' },
  { color: 'cyan', hex: '#06b6d4' },
  { color: 'orange', hex: '#f97316' },
  { color: 'indigo', hex: '#6366f1' },
  { color: 'green', hex: '#22c55e' },
];

const RADIUS_OPTIONS: { value: RadiusSize; label: string }[] = [
  { value: 'xs', label: 'XS' },
  { value: 'sm', label: 'SM' },
  { value: 'md', label: 'MD' },
  { value: 'lg', label: 'LG' },
  { value: 'xl', label: 'XL' },
];

export function ThemeDrawer() {
  const [opened, { open, close }] = useDisclosure(false);
  const {
    primaryColor,
    setPrimaryColor,
    colorScheme,
    toggleColorScheme,
    radius,
    setRadius,
    sidebarCollapsed,
    toggleSidebar,
  } = useThemeStore();
  const { setColorScheme: setMantineScheme } = useMantineColorScheme();

  const handleSchemeToggle = () => {
    toggleColorScheme();
    setMantineScheme(colorScheme === 'dark' ? 'light' : 'dark');
  };

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
          ⚙
        </ActionIcon>
      </Tooltip>

      <Drawer
        opened={opened}
        onClose={close}
        title="Theme Settings"
        position="right"
        size="xs"
        overlayProps={{ backgroundOpacity: 0.4, blur: 2 }}
      >
        <Stack gap="lg">
          {/* Primary Color */}
          <div>
            <Text size="sm" fw={600} mb="xs">Primary Color</Text>
            <Group gap="xs">
              {COLOR_OPTIONS.map((opt) => (
                <Tooltip label={opt.color} key={opt.color}>
                  <ColorSwatch
                    color={opt.hex}
                    onClick={() => setPrimaryColor(opt.color)}
                    style={{
                      cursor: 'pointer',
                      outline: primaryColor === opt.color
                        ? `2px solid ${opt.hex}`
                        : '2px solid transparent',
                      outlineOffset: 2,
                    }}
                  />
                </Tooltip>
              ))}
            </Group>
          </div>

          <Divider />

          {/* Color Scheme */}
          <div>
            <Text size="sm" fw={600} mb="xs">Color Scheme</Text>
            <Switch
              checked={colorScheme === 'dark'}
              onChange={handleSchemeToggle}
              label={colorScheme === 'dark' ? '🌙 Dark Mode' : '☀️ Light Mode'}
              size="md"
            />
          </div>

          <Divider />

          {/* Border Radius */}
          <div>
            <Text size="sm" fw={600} mb="xs">Border Radius</Text>
            <SegmentedControl
              value={radius}
              onChange={(v) => setRadius(v as RadiusSize)}
              data={RADIUS_OPTIONS}
              fullWidth
              size="xs"
            />
          </div>

          <Divider />

          {/* Sidebar */}
          <div>
            <Text size="sm" fw={600} mb="xs">Sidebar</Text>
            <Switch
              checked={sidebarCollapsed}
              onChange={toggleSidebar}
              label={sidebarCollapsed ? 'Collapsed' : 'Expanded'}
              size="md"
            />
          </div>
        </Stack>
      </Drawer>
    </>
  );
}
