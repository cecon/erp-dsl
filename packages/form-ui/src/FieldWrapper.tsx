import { Badge, Box, Group, Text, Tooltip, Alert } from '@mantine/core';
import { type ReactNode, useMemo } from 'react';

/* -----------------------------------------------------------------------
 * FieldWrapper
 *
 * Container de UX que envolve TODOS os campos do DSL form-ui.
 * Fornece:
 *  - Badge "Obrigatório" / "Opcional" ao lado do label
 *  - Contador de caracteres {n}/{maxLength} (quando maxLength existe)
 *  - Ícone de status: ✓ válido (verde) | ✗ inválido (vermelho)
 *  - Helper text via `description`
 *  - Slot de erro via `error`
 *  - DeprecationNotice: aviso com countdown quando deprecated=true
 * ----------------------------------------------------------------------- */

export interface FieldWrapperProps {
  /** Label principal do campo */
  label?: string;
  /**
   * Define se o campo é obrigatório/opcional para fins de UX.
   *  - true  → badge vermelho "Obrigatório"
   *  - false → badge cinza "Opcional"
   *  - undefined/omitido → sem badge (comportamento silencioso padrão)
   */
  required?: boolean;
  /** Limite máximo de caracteres — habilita o char counter */
  maxLength?: number;
  /** Comprimento atual do valor (string.length) */
  currentLength?: number;
  /** Mensagem de erro (vinda do form.getInputProps) */
  error?: string | null;
  /** Texto de ajuda exibido abaixo do input */
  description?: string;
  /**
   * Campo foi interagido pelo usuário?
   * Quando true + sem erro + tem valor → exibe ícone ✓
   */
  touched?: boolean;
  /** O campo tem valor preenchido? (qualquer truthy value) */
  hasValue?: boolean;
  /** O input renderizado */
  children: ReactNode;

  // ── Deprecação ────────────────────────────────────────────────────
  /** Campo está marcado como depreciado? */
  deprecated?: boolean;
  /** Data ISO (YYYY-MM-DD) em que o campo será removido */
  deprecatedAt?: string;
  /** Mensagem explicativa sobre a deprecação */
  deprecationMessage?: string;
}

/** Calcula a "saúde" do contador de caracteres. */
function counterColor(current: number, max: number): string {
  const pct = current / max;
  if (pct >= 1) return 'red';
  if (pct >= 0.9) return 'yellow.6';
  return 'dimmed';
}

/** Ícone SVG inline de ✓ (válido) ou ✗ (erro) com animação de entrada. */
function StatusIcon({ status }: { status: 'valid' | 'error' }) {
  const color = status === 'valid' ? 'var(--mantine-color-green-6)' : 'var(--mantine-color-red-6)';
  return (
    <Box
      component="span"
      aria-hidden="true"
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        animation: 'field-status-pop 0.2s ease-out',
      }}
    >
      <style>{`
        @keyframes field-status-pop {
          from { transform: scale(0.4); opacity: 0; }
          to   { transform: scale(1);   opacity: 1; }
        }
      `}</style>
      {status === 'valid' ? (
        <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
          <circle cx="8" cy="8" r="7.5" stroke={color} strokeWidth="1.5" fill="none" />
          <polyline
            points="4.5,8 7,10.5 11.5,5.5"
            stroke={color}
            strokeWidth="1.5"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        </svg>
      ) : (
        <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
          <circle cx="8" cy="8" r="7.5" stroke={color} strokeWidth="1.5" fill="none" />
          <line x1="5" y1="5" x2="11" y2="11" stroke={color} strokeWidth="1.5" strokeLinecap="round" />
          <line x1="11" y1="5" x2="5" y2="11" stroke={color} strokeWidth="1.5" strokeLinecap="round" />
        </svg>
      )}
    </Box>
  );
}

/** Calcula urgência e dias restantes de deprecação. */
function useDeprecationUrgency(deprecatedAt?: string) {
  return useMemo(() => {
    if (!deprecatedAt) return null;
    const target = new Date(deprecatedAt);
    const today = new Date();
    const diffMs = target.getTime() - today.getTime();
    const daysLeft = Math.ceil(diffMs / (1000 * 60 * 60 * 24));
    const formattedDate = target.toLocaleDateString('pt-BR', {
      day: '2-digit', month: '2-digit', year: 'numeric',
    });

    if (daysLeft < 0) return { level: 'expired' as const, daysLeft, formattedDate };
    if (daysLeft <= 30) return { level: 'critical' as const, daysLeft, formattedDate };
    if (daysLeft <= 90) return { level: 'warning' as const, daysLeft, formattedDate };
    return { level: 'info' as const, daysLeft, formattedDate };
  }, [deprecatedAt]);
}

/** Exibe o aviso de campo depreciado conforme urgência. */
function DeprecationNotice({
  deprecatedAt,
  deprecationMessage,
}: {
  deprecatedAt?: string;
  deprecationMessage?: string;
}) {
  const urgency = useDeprecationUrgency(deprecatedAt);
  if (!urgency) return null;

  if (urgency.level === 'expired') {
    return (
      <Alert color="red" radius="sm" mt={6} p="xs" styles={{ message: { fontSize: 12 } }}>
        🚫 <strong>Campo removido em {urgency.formattedDate}.</strong>{' '}
        {deprecationMessage ?? 'Este campo não está mais disponível.'}
      </Alert>
    );
  }

  if (urgency.level === 'critical') {
    return (
      <Alert color="orange" radius="sm" mt={6} p="xs" styles={{ message: { fontSize: 12 } }}>
        ⚠️ <strong>Faltam {urgency.daysLeft} dias</strong> — este campo será removido em{' '}
        <strong>{urgency.formattedDate}</strong>.{' '}
        {deprecationMessage && <span>{deprecationMessage}</span>}
      </Alert>
    );
  }

  if (urgency.level === 'warning') {
    return (
      <Alert color="yellow" radius="sm" mt={6} p="xs" styles={{ message: { fontSize: 12 } }}>
        🕐 Campo será descontinuado em <strong>{urgency.formattedDate}</strong>{' '}
        ({urgency.daysLeft} dias).{' '}
        {deprecationMessage && <span>{deprecationMessage}</span>}
      </Alert>
    );
  }

  // level === 'info': sutil, só tooltip no label
  return null;
}

/**
 * DSL FieldWrapper — container de UX para todos os campos do form-ui.
 */
export function FieldWrapper({
  label,
  required,
  maxLength,
  currentLength = 0,
  error,
  description,
  touched = false,
  hasValue = false,
  deprecated,
  deprecatedAt,
  deprecationMessage,
  children,
}: FieldWrapperProps) {
  const iconStatus: 'valid' | 'error' | 'idle' =
    error ? 'error' : touched && hasValue ? 'valid' : 'idle';

  const showCounter = typeof maxLength === 'number';
  const urgency = useDeprecationUrgency(deprecatedAt);

  // Borda lateral discreta para campos depreciados
  const deprecationBorderColor =
    urgency?.level === 'expired' ? 'var(--mantine-color-red-4)'
    : urgency?.level === 'critical' ? 'var(--mantine-color-orange-4)'
    : urgency?.level === 'warning' ? 'var(--mantine-color-yellow-4)'
    : undefined;

  return (
    <Box
      style={
        deprecated && deprecationBorderColor
          ? {
              borderLeft: `3px solid ${deprecationBorderColor}`,
              paddingLeft: 8,
              opacity: urgency?.level === 'expired' ? 0.7 : 1,
            }
          : undefined
      }
    >
      {/* ── Linha do Label ──────────────────────────────────────────── */}
      {(label || required !== undefined || showCounter || iconStatus !== 'idle') && (
        <Group justify="space-between" align="center" mb={4} wrap="nowrap">
          {/* Esquerda: label + badge + ícone de deprecação sutil */}
          <Group gap={6} align="center" style={{ flexShrink: 1, minWidth: 0 }}>
            {label && (
              <Text
                size="sm"
                fw={600}
                style={{
                  lineHeight: 1.4,
                  textDecoration: deprecated && urgency?.level === 'expired' ? 'line-through' : undefined,
                  color: deprecated && urgency?.level === 'expired' ? 'var(--mantine-color-dimmed)' : undefined,
                }}
              >
                {label}
              </Text>
            )}
            {deprecated && urgency?.level === 'info' && deprecatedAt && (
              <Tooltip
                label={`Descontinuado em ${new Date(deprecatedAt).toLocaleDateString('pt-BR')}${deprecationMessage ? ` — ${deprecationMessage}` : ''}`}
                withArrow
                multiline
                maw={280}
              >
                <Text component="span" size="xs" c="dimmed" style={{ cursor: 'help' }}>
                  🕐
                </Text>
              </Tooltip>
            )}
            {required === true && (
              <Badge size="xs" color="red" variant="light" radius="sm" style={{ flexShrink: 0 }}>
                Obrigatório
              </Badge>
            )}
            {required === false && (
              <Badge size="xs" color="gray" variant="light" radius="sm" style={{ flexShrink: 0 }}>
                Opcional
              </Badge>
            )}
          </Group>

          {/* Direita: contador + ícone de status */}
          <Group gap={6} align="center" style={{ flexShrink: 0 }}>
            {showCounter && (
              <Text size="xs" c={counterColor(currentLength, maxLength!)} ff="monospace">
                {currentLength}/{maxLength}
              </Text>
            )}
            {iconStatus !== 'idle' && <StatusIcon status={iconStatus} />}
          </Group>
        </Group>
      )}

      {/* ── Input (slot) ────────────────────────────────────────────── */}
      {children}

      {/* ── Footer: description + erro + deprecação ─────────────────── */}
      {description && !error && (
        <Text size="xs" c="dimmed" mt={4}>
          {description}
        </Text>
      )}
      {error && (
        <Text size="xs" c="red" mt={4} role="alert">
          {error}
        </Text>
      )}
      {deprecated && (
        <DeprecationNotice
          deprecatedAt={deprecatedAt}
          deprecationMessage={deprecationMessage}
        />
      )}
    </Box>
  );
}
