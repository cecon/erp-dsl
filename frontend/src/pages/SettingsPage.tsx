import {
  ActionIcon,
  Alert,
  Badge,
  Box,
  Button,
  Card,
  CopyButton,
  Divider,
  Group,
  Modal,
  Stack,
  Table,
  Text,
  TextInput,
  Title,
  Tooltip,
} from '@mantine/core';
import { useState } from 'react';
import { useApiTokens } from '../features/settings/useApiTokens';

function formatDate(iso: string | null) {
  if (!iso) return '—';
  return new Date(iso).toLocaleDateString('pt-BR', {
    day: '2-digit', month: '2-digit', year: 'numeric',
    hour: '2-digit', minute: '2-digit',
  });
}

export function SettingsPage() {
  const { tokens, loading, createToken, revokeToken } = useApiTokens();
  const [newTokenName, setNewTokenName] = useState('');
  const [creating, setCreating] = useState(false);
  const [createdToken, setCreatedToken] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleCreate = async () => {
    if (!newTokenName.trim()) return;
    setCreating(true);
    setError(null);
    try {
      const result = await createToken(newTokenName.trim());
      setCreatedToken(result.token);
      setNewTokenName('');
    } catch {
      setError('Erro ao criar token. Verifique e tente novamente.');
    } finally {
      setCreating(false);
    }
  };

  return (
    <Box maw={800} mx="auto" py="xl">
      <Title order={2} mb="xs">Configurações</Title>
      <Text c="dimmed" size="sm" mb="xl">
        Gerencie tokens de acesso para integrar o ERP com ferramentas externas como 
        ChatGPT, Claude, Cursor ou qualquer cliente que suporte OpenAPI / MCP.
      </Text>

      {/* ── Criar novo token ── */}
      <Card withBorder radius="md" p="lg" mb="xl">
        <Title order={4} mb="md">🔑 Tokens de API</Title>
        <Text size="sm" c="dimmed" mb="md">
          O token é exibido <strong>apenas uma vez</strong> no momento da criação. 
          Copie e guarde em local seguro antes de fechar a janela.
        </Text>

        <Group align="flex-end">
          <TextInput
            style={{ flex: 1 }}
            label="Nome do token"
            placeholder="Ex: ChatGPT, Cursor, Claude..."
            value={newTokenName}
            onChange={(e) => setNewTokenName(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleCreate()}
          />
          <Button
            onClick={handleCreate}
            loading={creating}
            disabled={!newTokenName.trim()}
            variant="filled"
          >
            Criar token
          </Button>
        </Group>

        {error && (
          <Alert color="red" mt="sm" radius="md">
            {error}
          </Alert>
        )}
      </Card>

      {/* ── Tokens existentes ── */}
      {loading ? (
        <Text c="dimmed" size="sm">Carregando tokens...</Text>
      ) : tokens.length === 0 ? (
        <Text c="dimmed" size="sm">Nenhum token criado ainda.</Text>
      ) : (
        <Card withBorder radius="md" p={0}>
          <Table highlightOnHover>
            <Table.Thead>
              <Table.Tr>
                <Table.Th>Nome</Table.Th>
                <Table.Th>Criado em</Table.Th>
                <Table.Th>Último uso</Table.Th>
                <Table.Th>Status</Table.Th>
                <Table.Th />
              </Table.Tr>
            </Table.Thead>
            <Table.Tbody>
              {tokens.map((t) => (
                <Table.Tr key={t.id}>
                  <Table.Td fw={500}>{t.name}</Table.Td>
                  <Table.Td><Text size="sm" c="dimmed">{formatDate(t.created_at)}</Text></Table.Td>
                  <Table.Td><Text size="sm" c="dimmed">{formatDate(t.last_used_at)}</Text></Table.Td>
                  <Table.Td>
                    <Badge color={t.is_active ? 'green' : 'gray'} size="sm">
                      {t.is_active ? 'Ativo' : 'Revogado'}
                    </Badge>
                  </Table.Td>
                  <Table.Td>
                    <Tooltip label="Revogar token">
                      <ActionIcon
                        color="red"
                        variant="subtle"
                        size="sm"
                        onClick={() => revokeToken(t.id)}
                        aria-label={`Revogar token ${t.name}`}
                      >
                        ✕
                      </ActionIcon>
                    </Tooltip>
                  </Table.Td>
                </Table.Tr>
              ))}
            </Table.Tbody>
          </Table>
        </Card>
      )}

      {/* ── Modal: token recém criado ── */}
      <Modal
        opened={!!createdToken}
        onClose={() => setCreatedToken(null)}
        title="Token criado com sucesso 🎉"
        centered
        size="lg"
      >
        <Stack>
          <Alert color="yellow" radius="md">
            ⚠️ Este token <strong>não será exibido novamente</strong>. 
            Copie e guarde em local seguro agora.
          </Alert>

          <Box
            p="md"
            style={{
              background: 'var(--mantine-color-dark-8, #0d1117)',
              borderRadius: 8,
              border: '1px solid var(--mantine-color-dark-4, #30363d)',
              fontFamily: 'monospace',
              wordBreak: 'break-all',
              fontSize: 13,
            }}
          >
            {createdToken}
          </Box>

          <CopyButton value={createdToken ?? ''} timeout={2000}>
            {({ copied, copy }) => (
              <Button
                onClick={copy}
                variant={copied ? 'filled' : 'outline'}
                color={copied ? 'green' : 'blue'}
                fullWidth
              >
                {copied ? '✓ Copiado!' : 'Copiar token'}
              </Button>
            )}
          </CopyButton>

          <Divider />

          <Text size="sm" c="dimmed" fw={500}>Como usar:</Text>
          <Stack gap="xs">
            <Text size="xs" c="dimmed">
              <strong>ChatGPT Actions</strong> → Autenticação → API Key → Tipo: Bearer → cole o token
            </Text>
            <Text size="xs" c="dimmed">
              <strong>Claude Desktop</strong> → claude_desktop_config.json → headers → X-API-Key: &lt;token&gt;
            </Text>
            <Text size="xs" c="dimmed">
              <strong>OpenAPI URL:</strong> https://mcp.c3bot.com/openapi.json
            </Text>
            <Text size="xs" c="dimmed">
              <strong>MCP SSE URL:</strong> https://mcp.c3bot.com/mcp/sse
            </Text>
          </Stack>
        </Stack>
      </Modal>
    </Box>
  );
}
