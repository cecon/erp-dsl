import { Badge, Button, Card, Group, Stack, Text, Title } from '@mantine/core';
import {
  IconCheck,
  IconCrown,
  IconRocket,
} from '@tabler/icons-react';
import { useNavigate } from 'react-router-dom';

const PLANS = [
  {
    name: 'Free',
    slug: 'free',
    price: 'R$ 0',
    period: '/mês',
    enabled: true,
    badge: null,
    cta: 'Começar Grátis',
    features: [
      '1 projeto',
      '1 app',
      '1.000 registros',
      'Banco de dados isolado',
      'Suporte comunidade',
    ],
    icon: IconRocket,
    gradient: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
  },
  {
    name: 'Pro',
    slug: 'pro',
    price: 'R$ 1.000',
    period: '/mês',
    enabled: false,
    badge: 'Em breve',
    cta: 'Em breve',
    features: [
      '10 projetos',
      '50 apps',
      'Registros ilimitados',
      'Banco de dados isolado',
      'Suporte prioritário',
      'LLM dedicada',
    ],
    icon: IconCrown,
    gradient: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)',
  },
];

export function PlanSelection() {
  const navigate = useNavigate();

  const handleSelect = (slug: string) => {
    if (slug === 'free') {
      navigate('/dashboard');
    }
  };

  return (
    <div className="plan-wrapper">
      <div className="plan-container">
        <Stack align="center" gap="xs" mb={40}>
          <Title order={2} c="white" fw={700}>
            Escolha seu plano
          </Title>
          <Text c="dimmed" size="md">
            Comece grátis e escale quando precisar
          </Text>
        </Stack>

        <Group gap="xl" justify="center" align="stretch">
          {PLANS.map((plan) => (
            <Card
              key={plan.slug}
              className={`plan-card ${!plan.enabled ? 'plan-card--disabled' : ''}`}
              padding="xl"
              radius="lg"
              w={340}
            >
              <Stack gap="lg">
                <Group justify="space-between">
                  <Group gap="xs">
                    <plan.icon size={24} stroke={1.5} />
                    <Text fw={700} size="lg">
                      {plan.name}
                    </Text>
                  </Group>
                  {plan.badge && (
                    <Badge variant="light" color="orange" size="sm">
                      {plan.badge}
                    </Badge>
                  )}
                </Group>

                <div>
                  <Text
                    fw={800}
                    size="xl"
                    style={{ fontSize: 36, lineHeight: 1 }}
                  >
                    {plan.price}
                  </Text>
                  <Text size="sm" c="dimmed" mt={4}>
                    {plan.period}
                  </Text>
                </div>

                <Stack gap="xs">
                  {plan.features.map((feat) => (
                    <Group key={feat} gap="xs" wrap="nowrap">
                      <IconCheck size={16} color="var(--mantine-color-teal-5)" />
                      <Text size="sm">{feat}</Text>
                    </Group>
                  ))}
                </Stack>

                <Button
                  fullWidth
                  size="md"
                  disabled={!plan.enabled}
                  onClick={() => handleSelect(plan.slug)}
                  mt="auto"
                  style={
                    plan.enabled
                      ? { background: plan.gradient }
                      : undefined
                  }
                >
                  {plan.cta}
                </Button>
              </Stack>
            </Card>
          ))}
        </Group>
      </div>
    </div>
  );
}
