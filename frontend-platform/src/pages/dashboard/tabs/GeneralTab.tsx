import { Card, Stack, TextInput } from '@mantine/core';

interface GeneralTabProps {
  project: {
    name: string;
    slug: string;
    created_at: string;
  } | null;
}

export function GeneralTab({ project }: GeneralTabProps) {
  return (
    <Card className="dash-card" padding="lg" radius="md">
      <Stack gap="md">
        <TextInput
          label="Nome do Projeto"
          value={project?.name || ''}
          readOnly
        />
        <TextInput label="Slug" value={project?.slug || ''} readOnly />
        <TextInput
          label="Criado em"
          value={
            project?.created_at
              ? new Date(project.created_at).toLocaleDateString('pt-BR')
              : ''
          }
          readOnly
        />
      </Stack>
    </Card>
  );
}
