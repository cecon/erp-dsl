import { Badge, Divider, Group, Text, Tooltip } from '@mantine/core';

/* eslint-disable @typescript-eslint/no-explicit-any */

interface RecordMetaBannerProps {
  /** Dados do registro sendo editado (ou {} para registro novo) */
  initialValues: Record<string, any>;
  /** Versão atual do schema que está renderizando este form */
  schemaVersion?: number;
  /** Está em modo de edição (true) ou criação (false/undefined)? */
  isEditMode?: boolean;
}

/** Formata uma data ISO para exibição local (DD/MM/YYYY). */
function formatDate(iso: string | undefined): string | null {
  if (!iso) return null;
  try {
    return new Date(iso).toLocaleDateString('pt-BR', {
      day: '2-digit', month: '2-digit', year: 'numeric',
    });
  } catch {
    return null;
  }
}

/** Formata uma data ISO de forma relativa ("há 3 dias", "há 2 horas"). */
function formatRelative(iso: string | undefined): string | null {
  if (!iso) return null;
  try {
    const diff = Date.now() - new Date(iso).getTime();
    const minutes = Math.floor(diff / 60_000);
    if (minutes < 1) return 'agora mesmo';
    if (minutes < 60) return `há ${minutes} min`;
    const hours = Math.floor(minutes / 60);
    if (hours < 24) return `há ${hours}h`;
    const days = Math.floor(hours / 24);
    if (days === 1) return 'há 1 dia';
    if (days < 30) return `há ${days} dias`;
    const months = Math.floor(days / 30);
    return months === 1 ? 'há 1 mês' : `há ${months} meses`;
  } catch {
    return null;
  }
}

/** Converte o valor de `active`/`status` em badge legível. */
function StatusBadge({ values }: { values: Record<string, any> }) {
  // Suporta: active (boolean), status (string draft/published/archived/active/inactive)
  const active = values.active;
  const status = values.status;

  if (typeof active === 'boolean') {
    return (
      <Badge
        size="xs"
        color={active ? 'green' : 'gray'}
        variant={active ? 'filled' : 'light'}
      >
        {active ? '● Ativo' : '○ Inativo'}
      </Badge>
    );
  }

  if (typeof status === 'string') {
    const config: Record<string, { color: string; label: string }> = {
      active:    { color: 'green', label: '● Ativo' },
      published: { color: 'green', label: '● Publicado' },
      draft:     { color: 'gray',  label: '○ Rascunho' },
      inactive:  { color: 'gray',  label: '○ Inativo' },
      archived:  { color: 'gray',  label: '○ Arquivado' },
    };
    const cfg = config[status];
    if (cfg) {
      return (
        <Badge size="xs" color={cfg.color} variant="light">
          {cfg.label}
        </Badge>
      );
    }
  }

  return null;
}

/**
 * RecordMetaBanner — rodapé de metadados de registro.
 *
 * Exibe abaixo dos botões de ação informações contextuais do registro:
 * status ativo/inativo, datas de criação e atualização, autor da última
 * alteração, e versão do schema. Lê campos por convenção (created_at,
 * updated_at, updated_by_name, active, status) — se não existirem, omite
 * silenciosamente.
 */
export function RecordMetaBanner({
  initialValues,
  schemaVersion,
  isEditMode,
}: RecordMetaBannerProps) {
  const createdAt = formatDate(initialValues.created_at);
  const updatedAt = formatRelative(initialValues.updated_at);
  const updatedAtFull = formatDate(initialValues.updated_at);
  const updatedBy = initialValues.updated_by_name ?? initialValues.updated_by ?? null;
  const hasAnyMeta = createdAt || updatedAt || updatedBy || schemaVersion;

  if (!hasAnyMeta) return null;

  return (
    <div>
      <Divider mt="md" mb="sm" />
      <Group gap="xs" align="center" wrap="wrap">
        {/* Status badge — só aparece em edição */}
        {isEditMode && <StatusBadge values={initialValues} />}

        {/* Criado em */}
        {isEditMode && createdAt && (
          <Text size="xs" c="dimmed">
            Criado em {createdAt}
          </Text>
        )}

        {/* Separador visual */}
        {isEditMode && createdAt && updatedAt && (
          <Text size="xs" c="dimmed">·</Text>
        )}

        {/* Atualizado em (relativo) com tooltip para data exata */}
        {isEditMode && updatedAt && (
          <Tooltip
            label={updatedAtFull ?? ''}
            withArrow
            disabled={!updatedAtFull}
          >
            <Text size="xs" c="dimmed" style={{ cursor: updatedAtFull ? 'help' : 'default' }}>
              Atualizado {updatedAt}
              {updatedBy && ` por ${updatedBy}`}
            </Text>
          </Tooltip>
        )}

        {/* Separador antes da versão */}
        {schemaVersion && (isEditMode && (createdAt || updatedAt)) && (
          <Text size="xs" c="dimmed">·</Text>
        )}

        {/* Versão do schema */}
        {schemaVersion && (
          <Tooltip label="Versão do schema deste formulário" withArrow>
            <Badge size="xs" color="blue" variant="dot" style={{ cursor: 'help' }}>
              Schema v{schemaVersion}
            </Badge>
          </Tooltip>
        )}
      </Group>
    </div>
  );
}
