import {
  Button,
  Card,
  SegmentedControl,
  Stack,
  TextInput,
} from '@mantine/core';
import { useForm } from '@mantine/form';
import { notifications } from '@mantine/notifications';
import { useState } from 'react';
import api from '../../../services/api';

interface CompanyTabProps {
  projectId: string;
  initialData: {
    type: string;
    razao_social: string;
    nome_fantasia: string;
    cnpj_cpf: string;
  } | null;
}

export function CompanyTab({ projectId, initialData }: CompanyTabProps) {
  const [saving, setSaving] = useState(false);

  const form = useForm({
    initialValues: {
      type: initialData?.type || 'pj',
      razao_social: initialData?.razao_social || '',
      nome_fantasia: initialData?.nome_fantasia || '',
      cnpj_cpf: initialData?.cnpj_cpf || '',
    },
  });

  const handleSave = async () => {
    setSaving(true);
    try {
      await api.post(
        `/api/accounts/projects/${projectId}/company`,
        form.values
      );
      notifications.show({
        title: 'Salvo',
        message: 'Dados da empresa atualizados com sucesso',
        color: 'teal',
      });
    } catch {
      notifications.show({
        title: 'Erro',
        message: 'Não foi possível salvar os dados da empresa',
        color: 'red',
      });
    } finally {
      setSaving(false);
    }
  };

  return (
    <Card className="dash-card" padding="lg" radius="md">
      <Stack gap="md">
        <SegmentedControl
          value={form.values.type}
          onChange={(v) => form.setFieldValue('type', v)}
          data={[
            { label: 'Pessoa Jurídica', value: 'pj' },
            { label: 'Pessoa Física', value: 'pf' },
          ]}
        />
        <TextInput
          label={
            form.values.type === 'pj' ? 'Razão Social' : 'Nome Completo'
          }
          {...form.getInputProps('razao_social')}
        />
        {form.values.type === 'pj' && (
          <TextInput
            label="Nome Fantasia"
            {...form.getInputProps('nome_fantasia')}
          />
        )}
        <TextInput
          label={form.values.type === 'pj' ? 'CNPJ' : 'CPF'}
          {...form.getInputProps('cnpj_cpf')}
        />
        <Button onClick={handleSave} loading={saving} w="fit-content">
          Salvar
        </Button>
      </Stack>
    </Card>
  );
}
