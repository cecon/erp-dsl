import {
  Badge,
  Button,
  Card,
  Grid,
  Group,
  Stack,
  Text,
} from '@mantine/core';
import { IconPlus, IconRocket } from '@tabler/icons-react';
import type { AppItem } from '../../../state/dashboardStore';

interface AppsTabProps {
  apps: AppItem[];
  onOpenCreateModal: () => void;
  onSelectApp: (appId: string) => void;
}

export function AppsTab({ apps, onOpenCreateModal, onSelectApp }: AppsTabProps) {
  return (
    <Stack gap="md">
      <Group justify="flex-end">
        <Button
          leftSection={<IconPlus size={16} />}
          onClick={onOpenCreateModal}
        >
          Novo App
        </Button>
      </Group>

      {apps.length === 0 ? (
        <Card className="dash-card" padding="xl" radius="md">
          <Stack align="center" gap="md">
            <IconRocket
              size={40}
              stroke={1}
              color="var(--mantine-color-dimmed)"
            />
            <Text c="dimmed">Nenhum app criado</Text>
            <Button onClick={onOpenCreateModal}>Criar App</Button>
          </Stack>
        </Card>
      ) : (
        <Grid>
          {apps.map((a) => (
            <Grid.Col key={a.id} span={6}>
              <Card
                className="dash-card"
                padding="lg"
                radius="md"
                style={{ cursor: 'pointer' }}
                onClick={() => onSelectApp(a.id)}
              >
                <Group justify="space-between" mb="xs">
                  <Text fw={600}>{a.name}</Text>
                  <Badge
                    variant="light"
                    color={a.status === 'active' ? 'teal' : 'gray'}
                    size="xs"
                  >
                    {a.status}
                  </Badge>
                </Group>
                <Text size="xs" c="dimmed">
                  {a.llm_provider || 'Sem LLM'} · {a.slug}
                </Text>
              </Card>
            </Grid.Col>
          ))}
        </Grid>
      )}
    </Stack>
  );
}
