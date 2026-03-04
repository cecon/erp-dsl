import {
  ActionIcon,
  Badge,
  Card,
  Code,
  CopyButton,
  Group,
  Loader,
  Stack,
  Text,
  Title,
  Tooltip,
  UnstyledButton,
} from '@mantine/core';
import {
  IconCheck,
  IconCopy,
  IconDatabase,
} from '@tabler/icons-react';
import { useState } from 'react';
import type { DatabaseInfo } from '../../../state/dashboardStore';

interface DatabaseTabProps {
  dbInfo: DatabaseInfo | null;
  selectedAppId: string | null;
  loading: boolean;
}

export function DatabaseTab({ dbInfo, selectedAppId, loading }: DatabaseTabProps) {
  if (!selectedAppId) {
    return (
      <Card className="dash-card" padding="xl" radius="md">
        <Stack align="center" gap="md">
          <IconDatabase
            size={40}
            stroke={1}
            color="var(--mantine-color-dimmed)"
          />
          <Text c="dimmed">
            Selecione um app na aba Apps para ver a conexão
          </Text>
        </Stack>
      </Card>
    );
  }

  if (loading || !dbInfo) {
    return (
      <Card className="dash-card" padding="xl" radius="md">
        <Stack align="center" gap="md">
          <Loader size="sm" />
          <Text c="dimmed">Carregando...</Text>
        </Stack>
      </Card>
    );
  }

  return (
    <Card className="dash-card" padding="lg" radius="md">
      <Stack gap="md">
        <Group justify="space-between">
          <Title order={5}>Conexão do Banco</Title>
          <Badge
            color={dbInfo.status === 'ready' ? 'teal' : 'orange'}
          >
            {dbInfo.status}
          </Badge>
        </Group>

        <DbField label="Host" value={dbInfo.db_host} />
        <DbField label="Port" value={String(dbInfo.db_port)} />
        <DbField label="Database" value={dbInfo.db_name} />
        <DbField label="User" value={dbInfo.db_user} />
        <DbField label="Password" value={dbInfo.db_password} secret />

        <Text size="xs" c="dimmed" mt="sm">
          Connection string:
        </Text>
        <Code block>
          {`postgresql://${dbInfo.db_user}:${dbInfo.db_password}@${dbInfo.db_host}:${dbInfo.db_port}/${dbInfo.db_name}`}
        </Code>
      </Stack>
    </Card>
  );
}

/* ── Helper component ───────────────────────────────────── */

function DbField({
  label,
  value,
  secret,
}: {
  label: string;
  value: string;
  secret?: boolean;
}) {
  const [show, setShow] = useState(!secret);

  return (
    <Group gap="xs" wrap="nowrap">
      <Text size="sm" fw={500} w={90}>
        {label}
      </Text>
      <Code style={{ flex: 1 }}>{show ? value : '••••••••••'}</Code>
      {secret && (
        <UnstyledButton onClick={() => setShow(!show)}>
          <Text size="xs" c="blue">
            {show ? 'Ocultar' : 'Mostrar'}
          </Text>
        </UnstyledButton>
      )}
      <CopyButton value={value}>
        {({ copied, copy }) => (
          <Tooltip label={copied ? 'Copiado!' : 'Copiar'}>
            <ActionIcon variant="subtle" size="sm" onClick={copy}>
              {copied ? <IconCheck size={14} /> : <IconCopy size={14} />}
            </ActionIcon>
          </Tooltip>
        )}
      </CopyButton>
    </Group>
  );
}
