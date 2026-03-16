import { Alert, Badge, Button, Group, Loader, Stack, Text, Tooltip } from '@mantine/core';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useEngine } from './EngineProvider';

/* eslint-disable @typescript-eslint/no-explicit-any */

interface VersionStatus {
  scope: 'global' | 'tenant';
  tenant_version: number | null;
  tenant_version_id: string | null;
  global_version: number | null;
  global_version_id: string | null;
  has_updates: boolean;
}

interface Props {
  pageKey: string;
}

/**
 * Banner de gestão de versões de schema.
 *
 * Exibido apenas para usuários com role="admin" quando a página usa
 * um schema customizado pelo tenant (scope="tenant").
 *
 * Permite:
 * - Ver a versão atual vs global
 * - Mesclar atualizações do global no schema do tenant
 * - Reverter ao schema global padrão
 */
export function SchemaVersionBanner({ pageKey }: Props) {
  const { apiClient, userRole } = useEngine();
  const queryClient = useQueryClient();

  // Só exibe para admins
  if (userRole !== 'admin') return null;

  const { data: status, isLoading } = useQuery<VersionStatus>({
    queryKey: ['version-status', pageKey],
    queryFn: () =>
      apiClient.get(`/pages/${pageKey}/version-status`).then((r) => r.data),
    staleTime: 30_000,
  });

  const invalidate = () => {
    queryClient.invalidateQueries({ queryKey: ['page', pageKey] });
    queryClient.invalidateQueries({ queryKey: ['version-status', pageKey] });
    // Dispara evento para o PageRenderer recarregar o schema
    window.dispatchEvent(new Event('otto:refresh-page'));
  };

  const mergeMutation = useMutation({
    mutationFn: () =>
      apiClient.post(`/pages/${pageKey}/merge`).then((r) => r.data),
    onSuccess: invalidate,
    onError: (err: any) => {
      console.error('[SchemaVersionBanner] merge error', err);
      alert('Erro ao mesclar: ' + (err?.response?.data?.detail ?? err.message));
    },
  });

  const rollbackMutation = useMutation({
    mutationFn: () =>
      apiClient
        .post(`/pages/${pageKey}/rollback/${status?.global_version_id}`)
        .then((r) => r.data),
    onSuccess: invalidate,
    onError: (err: any) => {
      console.error('[SchemaVersionBanner] rollback error', err);
      alert('Erro ao reverter: ' + (err?.response?.data?.detail ?? err.message));
    },
  });

  if (isLoading) {
    return (
      <Group gap="xs" justify="flex-end">
        <Loader size="xs" color="gray" />
      </Group>
    );
  }

  // Schema global — sem customização, sem banner
  if (!status || status.scope === 'global') return null;

  const isBusy = mergeMutation.isPending || rollbackMutation.isPending;

  // Tenant customizado sem updates pendentes — badge sutil
  if (!status.has_updates) {
    return (
      <Group justify="flex-end" mb="xs">
        <Tooltip label="Este formulário tem um schema personalizado para seu tenant" withArrow>
          <Badge variant="light" color="gray" size="sm" style={{ cursor: 'default' }}>
            🔧 Schema personalizado · v{status.tenant_version}
          </Badge>
        </Tooltip>
      </Group>
    );
  }

  // Tenant customizado COM updates disponíveis — alert de ação
  return (
    <Alert
      color="yellow"
      radius="md"
      mb="md"
      title={
        <Group gap="xs">
          <Text fw={600} size="sm">Schema personalizado · v{status.tenant_version}</Text>
          <Badge color="orange" size="sm" variant="filled">
            Global em v{status.global_version}
          </Badge>
        </Group>
      }
    >
      <Stack gap="xs">
        <Text size="sm" c="dimmed">
          Este formulário foi personalizado. O schema global foi atualizado e há
          melhorias disponíveis. Você pode mesclar as novidades mantendo suas
          customizações, ou reverter ao padrão global.
        </Text>
        <Group gap="sm">
          <Button
            size="xs"
            variant="filled"
            color="orange"
            loading={mergeMutation.isPending}
            disabled={isBusy}
            onClick={() => {
              if (confirm('Mesclar schema global no seu schema personalizado? Um novo draft será criado.')) {
                mergeMutation.mutate();
              }
            }}
          >
            ⬆ Mesclar com global
          </Button>
          <Button
            size="xs"
            variant="light"
            color="gray"
            loading={rollbackMutation.isPending}
            disabled={isBusy}
            onClick={() => {
              if (confirm('Reverter ao schema global padrão? Sua personalização será removida.')) {
                rollbackMutation.mutate();
              }
            }}
          >
            ↩ Reverter ao global
          </Button>
        </Group>
      </Stack>
    </Alert>
  );
}
