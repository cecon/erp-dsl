import { Alert, Badge, Button, Group, Text } from '@mantine/core';
import { useState, useEffect } from 'react';

interface FormVersionSwitcherProps {
  pageKey: string;
  /** Versão atualmente renderizada */
  currentVersion: number;
  /** Versão mais recente disponível (global ou tenant) */
  latestVersion: number;
  /** Callback para troca de versão */
  onVersionChange: (version: number) => void;
}

const PREF_KEY = (pageKey: string) => `form_version_pref_${pageKey}`;

/**
 * FormVersionSwitcher — permite ao usuário experimentar uma nova versão
 * do formulário e voltar à anterior com um clique.
 *
 * A preferência é salva em localStorage por pageKey.
 * Nenhuma escrita no banco — é puramente client-side.
 *
 * Exibido para TODOS os usuários (não requer role admin).
 */
export function FormVersionSwitcher({
  pageKey,
  currentVersion,
  latestVersion,
  onVersionChange,
}: FormVersionSwitcherProps) {
  const [dismissed, setDismissed] = useState(false);
  const [tryingNew, setTryingNew] = useState(false);

  // Recupera preferência salva
  useEffect(() => {
    const savedPref = localStorage.getItem(PREF_KEY(pageKey));
    if (savedPref === 'new') {
      setTryingNew(true);
      // Se já está em modo novo mas o componente está renderizando a versão antiga
      if (currentVersion < latestVersion) {
        onVersionChange(latestVersion);
      }
    }
  }, [pageKey]); // eslint-disable-line react-hooks/exhaustive-deps

  const hasNewVersion = latestVersion > currentVersion;

  // Usuário já está na nova versão — modo "beta ativo"
  if (tryingNew && currentVersion === latestVersion) {
    return (
      <Alert
        color="blue"
        radius="md"
        mb="sm"
        styles={{ root: { borderStyle: 'dashed' } }}
      >
        <Group justify="space-between" align="center" wrap="nowrap">
          <Group gap="xs">
            <Badge color="blue" size="sm" variant="filled">🧪 Beta</Badge>
            <Text size="sm">Você está visualizando a versão nova deste formulário</Text>
          </Group>
          <Button
            size="xs"
            variant="subtle"
            color="gray"
            onClick={() => {
              localStorage.setItem(PREF_KEY(pageKey), 'old');
              setTryingNew(false);
              onVersionChange(currentVersion - 1);
            }}
          >
            ← Voltar à versão anterior
          </Button>
        </Group>
      </Alert>
    );
  }

  // Nova versão disponível, ainda não viu ou não dispensou
  if (hasNewVersion && !dismissed && !tryingNew) {
    return (
      <Alert
        color="violet"
        radius="md"
        mb="sm"
        title={
          <Group gap="xs" align="center">
            <Badge color="violet" size="sm" variant="filled">✨ NEW</Badge>
            <Text size="sm" fw={600}>Nova versão deste formulário disponível</Text>
          </Group>
        }
        withCloseButton
        onClose={() => {
          setDismissed(true);
          // Não salva preferência — só esconde nesta sessão
        }}
      >
        <Group justify="space-between" align="center" mt={4}>
          <Text size="xs" c="dimmed">
            Versão {latestVersion} disponível · Experimente sem compromisso, você pode voltar a qualquer momento
          </Text>
          <Button
            size="xs"
            variant="light"
            color="violet"
            onClick={() => {
              localStorage.setItem(PREF_KEY(pageKey), 'new');
              setTryingNew(true);
              onVersionChange(latestVersion);
            }}
          >
            Experimentar nova versão
          </Button>
        </Group>
      </Alert>
    );
  }

  return null;
}

/** Lê a preferência de versão do localStorage para um pageKey. */
export function getVersionPreference(pageKey: string): 'new' | 'old' | null {
  try {
    return (localStorage.getItem(PREF_KEY(pageKey)) as 'new' | 'old') ?? null;
  } catch {
    return null;
  }
}
