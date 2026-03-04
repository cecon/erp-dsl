import { Button, Modal, Stack, Text, TextInput } from '@mantine/core';
import { useForm } from '@mantine/form';
import { notifications } from '@mantine/notifications';
import { useState } from 'react';
import api from '../../services/api';
import type { AppItem } from '../../state/dashboardStore';

interface CreateAppModalProps {
  projectId: string;
  opened: boolean;
  onClose: () => void;
  onCreated: (app: AppItem) => void;
}

export function CreateAppModal({
  projectId,
  opened,
  onClose,
  onCreated,
}: CreateAppModalProps) {
  const [creating, setCreating] = useState(false);

  const form = useForm({
    initialValues: {
      name: '',
      llm_provider: '',
      llm_model: '',
      llm_api_key: '',
    },
    validate: {
      name: (v: string) => (v.trim().length < 1 ? 'Nome é obrigatório' : null),
    },
  });

  const handleSubmit = async (values: typeof form.values) => {
    setCreating(true);
    try {
      const { data } = await api.post(
        `/api/accounts/projects/${projectId}/apps`,
        {
          name: values.name,
          llm_provider: values.llm_provider || null,
          llm_model: values.llm_model || null,
          llm_api_key: values.llm_api_key || null,
        }
      );
      onCreated(data);
      form.reset();
      onClose();
    } catch {
      notifications.show({
        title: 'Erro',
        message: 'Não foi possível criar o app',
        color: 'red',
      });
    } finally {
      setCreating(false);
    }
  };

  return (
    <Modal opened={opened} onClose={onClose} title="Novo App" centered size="md">
      <form onSubmit={form.onSubmit(handleSubmit)}>
        <Stack gap="md">
          <TextInput
            label="Nome do App"
            placeholder="meu-app"
            data-autofocus
            {...form.getInputProps('name')}
          />
          <TextInput
            label="LLM Provider"
            placeholder="openai, groq, ollama..."
            {...form.getInputProps('llm_provider')}
          />
          <TextInput
            label="LLM Model"
            placeholder="gpt-4o-mini"
            {...form.getInputProps('llm_model')}
          />
          <TextInput
            label="API Key"
            placeholder="sk-..."
            {...form.getInputProps('llm_api_key')}
          />
          <Text size="xs" c="dimmed">
            Um banco de dados isolado será criado automaticamente
          </Text>
          <Button
            type="submit"
            fullWidth
            loading={creating}
            disabled={!form.values.name.trim()}
          >
            Criar App
          </Button>
        </Stack>
      </form>
    </Modal>
  );
}
