import {
  ActionIcon,
  Badge,
  Button,
  Card,
  Code,
  CopyButton,
  Grid,
  Group,
  Loader,
  Modal,
  SegmentedControl,
  Stack,
  Tabs,
  Text,
  TextInput,
  Title,
  Tooltip,
  UnstyledButton,
} from '@mantine/core';
import {
  IconArrowLeft,
  IconBuildingStore,
  IconCheck,
  IconCopy,
  IconDatabase,
  IconPlus,
  IconRocket,
  IconSettings,
} from '@tabler/icons-react';
import { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import api from '../../services/api';
import type { AppItem, DatabaseInfo } from '../../state/dashboardStore';

export function ProjectSettings() {
  const { projectId } = useParams<{ projectId: string }>();
  const navigate = useNavigate();
  const [project, setProject] = useState<any>(null);
  const [apps, setApps] = useState<AppItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [dbInfo, setDbInfo] = useState<DatabaseInfo | null>(null);
  const [selectedAppId, setSelectedAppId] = useState<string | null>(null);

  // Company form
  const [companyType, setCompanyType] = useState('pj');
  const [companyName, setCompanyName] = useState('');
  const [companyFantasia, setCompanyFantasia] = useState('');
  const [companyCnpjCpf, setCompanyCnpjCpf] = useState('');
  const [savingCompany, setSavingCompany] = useState(false);

  // App creation modal
  const [appModal, setAppModal] = useState(false);
  const [newAppName, setNewAppName] = useState('');
  const [llmProvider, setLlmProvider] = useState('');
  const [llmModel, setLlmModel] = useState('');
  const [llmApiKey, setLlmApiKey] = useState('');
  const [creatingApp, setCreatingApp] = useState(false);

  useEffect(() => {
    if (!projectId) return;
    Promise.all([
      api.get(`/api/accounts/projects/${projectId}`),
      api.get(`/api/accounts/projects/${projectId}/apps`),
      api.get(`/api/accounts/projects/${projectId}/company`).catch(() => ({
        data: null,
      })),
    ])
      .then(([pRes, aRes, cRes]) => {
        setProject(pRes.data);
        setApps(aRes.data);
        if (cRes.data) {
          setCompanyType(cRes.data.type || 'pj');
          setCompanyName(cRes.data.razao_social || '');
          setCompanyFantasia(cRes.data.nome_fantasia || '');
          setCompanyCnpjCpf(cRes.data.cnpj_cpf || '');
        }
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [projectId]);

  const handleSaveCompany = async () => {
    setSavingCompany(true);
    try {
      await api.post(`/api/accounts/projects/${projectId}/company`, {
        type: companyType,
        razao_social: companyName,
        nome_fantasia: companyFantasia,
        cnpj_cpf: companyCnpjCpf,
      });
    } catch {
      // handled
    } finally {
      setSavingCompany(false);
    }
  };

  const handleCreateApp = async () => {
    if (!newAppName.trim()) return;
    setCreatingApp(true);
    try {
      const { data } = await api.post(
        `/api/accounts/projects/${projectId}/apps`,
        {
          name: newAppName,
          llm_provider: llmProvider || null,
          llm_model: llmModel || null,
          llm_api_key: llmApiKey || null,
        }
      );
      setApps((prev) => [...prev, data]);
      setAppModal(false);
      setNewAppName('');
      setLlmProvider('');
      setLlmModel('');
      setLlmApiKey('');
    } catch {
      // handled
    } finally {
      setCreatingApp(false);
    }
  };

  const loadDbInfo = async (appId: string) => {
    setSelectedAppId(appId);
    try {
      const { data } = await api.get(`/api/accounts/apps/${appId}/database`);
      setDbInfo(data);
    } catch {
      setDbInfo(null);
    }
  };

  if (loading) {
    return (
      <Group justify="center" py={80}>
        <Loader />
      </Group>
    );
  }

  return (
    <div className="dash-layout">
      <main className="dash-main" style={{ maxWidth: 960, margin: '0 auto' }}>
        <Group mb="lg" gap="xs">
          <UnstyledButton onClick={() => navigate('/')}>
            <IconArrowLeft size={20} />
          </UnstyledButton>
          <Title order={3} fw={600}>
            {project?.name || 'Projeto'}
          </Title>
          <Badge variant="light" color="teal" size="sm">
            {project?.status}
          </Badge>
        </Group>

        <Tabs defaultValue="general" variant="outline">
          <Tabs.List mb="lg">
            <Tabs.Tab value="general" leftSection={<IconSettings size={16} />}>
              Geral
            </Tabs.Tab>
            <Tabs.Tab
              value="company"
              leftSection={<IconBuildingStore size={16} />}
            >
              Empresa
            </Tabs.Tab>
            <Tabs.Tab value="apps" leftSection={<IconRocket size={16} />}>
              Apps
            </Tabs.Tab>
            <Tabs.Tab value="database" leftSection={<IconDatabase size={16} />}>
              Database
            </Tabs.Tab>
          </Tabs.List>

          {/* General */}
          <Tabs.Panel value="general">
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
          </Tabs.Panel>

          {/* Company */}
          <Tabs.Panel value="company">
            <Card className="dash-card" padding="lg" radius="md">
              <Stack gap="md">
                <SegmentedControl
                  value={companyType}
                  onChange={setCompanyType}
                  data={[
                    { label: 'Pessoa Jurídica', value: 'pj' },
                    { label: 'Pessoa Física', value: 'pf' },
                  ]}
                />
                <TextInput
                  label={
                    companyType === 'pj' ? 'Razão Social' : 'Nome Completo'
                  }
                  value={companyName}
                  onChange={(e) => setCompanyName(e.currentTarget.value)}
                />
                {companyType === 'pj' && (
                  <TextInput
                    label="Nome Fantasia"
                    value={companyFantasia}
                    onChange={(e) => setCompanyFantasia(e.currentTarget.value)}
                  />
                )}
                <TextInput
                  label={companyType === 'pj' ? 'CNPJ' : 'CPF'}
                  value={companyCnpjCpf}
                  onChange={(e) => setCompanyCnpjCpf(e.currentTarget.value)}
                />
                <Button
                  onClick={handleSaveCompany}
                  loading={savingCompany}
                  w="fit-content"
                >
                  Salvar
                </Button>
              </Stack>
            </Card>
          </Tabs.Panel>

          {/* Apps */}
          <Tabs.Panel value="apps">
            <Stack gap="md">
              <Group justify="flex-end">
                <Button
                  leftSection={<IconPlus size={16} />}
                  onClick={() => setAppModal(true)}
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
                    <Button onClick={() => setAppModal(true)}>
                      Criar App
                    </Button>
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
                        onClick={() => loadDbInfo(a.id)}
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
          </Tabs.Panel>

          {/* Database */}
          <Tabs.Panel value="database">
            {!selectedAppId ? (
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
            ) : !dbInfo ? (
              <Card className="dash-card" padding="xl" radius="md">
                <Stack align="center" gap="md">
                  <Loader size="sm" />
                  <Text c="dimmed">Carregando...</Text>
                </Stack>
              </Card>
            ) : (
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
                  <DbField
                    label="Password"
                    value={dbInfo.db_password}
                    secret
                  />

                  <Text size="xs" c="dimmed" mt="sm">
                    Connection string:
                  </Text>
                  <Code block>
                    {`postgresql://${dbInfo.db_user}:${dbInfo.db_password}@${dbInfo.db_host}:${dbInfo.db_port}/${dbInfo.db_name}`}
                  </Code>
                </Stack>
              </Card>
            )}
          </Tabs.Panel>
        </Tabs>
      </main>

      {/* Create App Modal */}
      <Modal
        opened={appModal}
        onClose={() => setAppModal(false)}
        title="Novo App"
        centered
        size="md"
      >
        <Stack gap="md">
          <TextInput
            label="Nome do App"
            placeholder="meu-app"
            value={newAppName}
            onChange={(e) => setNewAppName(e.currentTarget.value)}
            data-autofocus
          />
          <TextInput
            label="LLM Provider"
            placeholder="openai, groq, ollama..."
            value={llmProvider}
            onChange={(e) => setLlmProvider(e.currentTarget.value)}
          />
          <TextInput
            label="LLM Model"
            placeholder="gpt-4o-mini"
            value={llmModel}
            onChange={(e) => setLlmModel(e.currentTarget.value)}
          />
          <TextInput
            label="API Key"
            placeholder="sk-..."
            value={llmApiKey}
            onChange={(e) => setLlmApiKey(e.currentTarget.value)}
          />
          <Text size="xs" c="dimmed">
            Um banco de dados isolado será criado automaticamente
          </Text>
          <Button
            fullWidth
            loading={creatingApp}
            onClick={handleCreateApp}
            disabled={!newAppName.trim()}
          >
            Criar App
          </Button>
        </Stack>
      </Modal>
    </div>
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
