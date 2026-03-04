import { useState } from 'react';
import { Badge, Code, Group, SimpleGrid, Text, Title } from '@mantine/core';
import { componentRegistry } from '../core/engine/ComponentRegistry';

/* eslint-disable @typescript-eslint/no-explicit-any */

/* ── Component metadata ─────────────────────────────────────────── */

interface ComponentMeta {
  type: string;
  label: string;
  description: string;
  category: 'input' | 'special' | 'internal';
  /** Default props used in the live preview */
  defaultProps?: Record<string, any>;
  /** Example DSL schema snippet */
  dslExample: Record<string, any>;
}

const COMPONENT_META: ComponentMeta[] = [
  {
    type: 'text',
    label: 'TextField',
    description: 'Campo de texto padrão. Aceita qualquer string livre. Ideal para nomes, códigos e campos curtos.',
    category: 'input',
    defaultProps: { label: 'Nome do Produto', placeholder: 'Ex: Widget Pro' },
    dslExample: { id: 'name', type: 'text', label: 'Nome do Produto' },
  },
  {
    type: 'number',
    label: 'NumberField',
    description: 'Campo numérico com separadores BR (ponto para milhar, vírgula para decimal). Não aceita valores negativos por padrão.',
    category: 'input',
    defaultProps: { label: 'Quantidade', placeholder: '0' },
    dslExample: { id: 'qty', type: 'number', label: 'Quantidade' },
  },
  {
    type: 'money',
    label: 'MoneyField',
    description: 'Campo monetário pré-configurado para BRL: prefixo R$, 2 casas decimais, separadores brasileiros.',
    category: 'input',
    defaultProps: { label: 'Preço de Venda', placeholder: 'R$ 0,00' },
    dslExample: { id: 'price', type: 'money', label: 'Preço de Venda' },
  },
  {
    type: 'date',
    label: 'DateField',
    description: 'Seletor de data nativo (HTML date input). Valor no formato ISO 8601: YYYY-MM-DD.',
    category: 'input',
    defaultProps: { label: 'Data de Emissão' },
    dslExample: { id: 'issue_date', type: 'date', label: 'Data de Emissão' },
  },
  {
    type: 'datetime',
    label: 'DateTimeField',
    description: 'Seletor de data e hora nativo (datetime-local). Valor no formato ISO 8601 local: YYYY-MM-DDTHH:mm.',
    category: 'input',
    defaultProps: { label: 'Data e Hora de Entrega' },
    dslExample: { id: 'delivery_at', type: 'datetime', label: 'Data e Hora de Entrega' },
  },
  {
    type: 'select',
    label: 'SelectField',
    description: 'Dropdown com busca e limpeza. Suporta opções estáticas (via options) ou dinâmicas (via dataSource + dataSourceParams).',
    category: 'input',
    defaultProps: {
      label: 'Unidade de Medida',
      options: [
        { value: 'UN', label: 'UN — Unidade' },
        { value: 'KG', label: 'KG — Quilograma' },
        { value: 'LT', label: 'LT — Litro' },
        { value: 'MT', label: 'MT — Metro' },
      ],
    },
    dslExample: {
      id: 'unidade',
      type: 'select',
      label: 'Unidade de Medida',
      options: [
        { value: 'UN', label: 'UN — Unidade' },
        { value: 'KG', label: 'KG — Quilograma' },
      ],
    },
  },
  {
    type: 'checkbox',
    label: 'CheckboxField',
    description: 'Checkbox booleano. Emite true/false diretamente via onChange.',
    category: 'input',
    defaultProps: { label: 'Produto ativo' },
    dslExample: { id: 'active', type: 'checkbox', label: 'Produto ativo' },
  },
  {
    type: 'textarea',
    label: 'TextAreaField',
    description: 'Campo de texto multilinha com auto-resize (min 3, max 8 linhas). Ideal para descrições longas.',
    category: 'input',
    defaultProps: { label: 'Descrição Comercial', placeholder: 'Descreva o produto...' },
    dslExample: { id: 'description', type: 'textarea', label: 'Descrição Comercial' },
  },
  {
    type: 'color_swatch_picker',
    label: 'ColorSwatchPicker',
    description: 'Seletor visual de cores via swatches. Cada opção define value (nome da cor) e hex (código hex para exibição).',
    category: 'input',
    defaultProps: {
      label: 'Cor do Tema',
      options: [
        { value: 'blue', hex: '#3b82f6' },
        { value: 'green', hex: '#10b981' },
        { value: 'red', hex: '#ef4444' },
        { value: 'purple', hex: '#8b5cf6' },
        { value: 'orange', hex: '#f59e0b' },
      ],
    },
    dslExample: {
      id: 'theme_color',
      type: 'color_swatch_picker',
      label: 'Cor do Tema',
      options: [{ value: 'blue', hex: '#3b82f6' }],
    },
  },
  {
    type: 'theme_switch',
    label: 'ThemeSwitch',
    description: 'Toggle switch. Modo booleano (true/false) ou modo string (emite on_value/off_value customizados).',
    category: 'input',
    defaultProps: {
      label: 'Modo Escuro',
      on_label: 'Escuro',
      off_label: 'Claro',
    },
    dslExample: {
      id: 'dark_mode',
      type: 'theme_switch',
      label: 'Modo Escuro',
      on_label: 'Escuro',
      off_label: 'Claro',
    },
  },
  {
    type: 'segmented',
    label: 'SegmentedField',
    description: 'Controle segmentado (group de botões mutuamente exclusivos). Cada opção tem value + label opcional.',
    category: 'input',
    defaultProps: {
      label: 'Status',
      options: [
        { value: 'active', label: 'Ativo' },
        { value: 'inactive', label: 'Inativo' },
        { value: 'draft', label: 'Rascunho' },
      ],
    },
    dslExample: {
      id: 'status',
      type: 'segmented',
      label: 'Status',
      options: [
        { value: 'active', label: 'Ativo' },
        { value: 'inactive', label: 'Inativo' },
      ],
    },
  },
  {
    type: 'hidden',
    label: 'Hidden',
    description: 'Campo oculto. Não renderiza nada visualmente. Usado para armazenar valores internos no form.',
    category: 'internal',
    dslExample: { id: 'tenant_id', type: 'hidden' },
  },
  {
    type: 'agent:product-enrich',
    label: 'ProductEnrichModal',
    description: 'Modal de enriquecimento de produto via IA. Componente especial acionado por actions do tipo "agent".',
    category: 'special',
    dslExample: { id: 'enrich', type: 'agent:product-enrich' },
  },
  {
    type: 'workflow_step_editor',
    label: 'WorkflowStepEditor',
    description: 'Editor visual de steps de workflow. Componente especializado para a tela de automação.',
    category: 'special',
    dslExample: { id: 'steps', type: 'workflow_step_editor' },
  },
];

/* ── Component card with live preview ────────────────────────────── */

function ComponentCard({ meta }: { meta: ComponentMeta }) {
  const Component = componentRegistry[meta.type];
  const [value, setValue] = useState<any>(meta.type === 'checkbox' ? false : '');

  const isPreviewable = meta.category === 'input' && Component;

  const categoryColors: Record<string, string> = {
    input: 'blue',
    special: 'grape',
    internal: 'gray',
  };

  const categoryLabels: Record<string, string> = {
    input: 'Input',
    special: 'Especial',
    internal: 'Interno',
  };

  return (
    <div className="showcase-card">
      <div className="showcase-card-header">
        <Group justify="space-between" align="flex-start">
          <div>
            <Text className="showcase-card-title">{meta.label}</Text>
            <Code className="showcase-card-type">{meta.type}</Code>
          </div>
          <Badge
            size="sm"
            variant="light"
            color={categoryColors[meta.category]}
          >
            {categoryLabels[meta.category]}
          </Badge>
        </Group>
        <Text className="showcase-card-desc" mt="xs">
          {meta.description}
        </Text>
      </div>

      {isPreviewable && (
        <div className="showcase-preview">
          <Text className="showcase-section-label">Preview</Text>
          <div className="showcase-preview-area">
            <Component
              {...meta.defaultProps}
              value={value}
              onChange={setValue}
            />
          </div>
        </div>
      )}

      <div className="showcase-schema">
        <Text className="showcase-section-label">Schema DSL</Text>
        <Code block className="showcase-code">
          {JSON.stringify(meta.dslExample, null, 2)}
        </Code>
      </div>
    </div>
  );
}

/* ── Main Page ──────────────────────────────────────────────────── */

export function ComponentShowcase() {
  const totalRegistered = Object.keys(componentRegistry).length;
  const inputCount = COMPONENT_META.filter((m) => m.category === 'input').length;
  const specialCount = COMPONENT_META.filter((m) => m.category !== 'input').length;

  return (
    <div className="fade-in" style={{ padding: '0 4px' }}>
      {/* Page header */}
      <div className="page-header">
        <div>
          <h1 className="page-header-title">Component Showcase</h1>
          <p className="page-header-subtitle">
            Catálogo de todos os componentes registrados no ComponentRegistry
          </p>
        </div>
      </div>

      {/* Stats */}
      <Group gap="lg" mb="xl">
        <div className="showcase-stat">
          <Text className="showcase-stat-value">{totalRegistered}</Text>
          <Text className="showcase-stat-label">Registrados</Text>
        </div>
        <div className="showcase-stat">
          <Text className="showcase-stat-value">{inputCount}</Text>
          <Text className="showcase-stat-label">Inputs</Text>
        </div>
        <div className="showcase-stat">
          <Text className="showcase-stat-value">{specialCount}</Text>
          <Text className="showcase-stat-label">Especiais</Text>
        </div>
      </Group>

      {/* Input components */}
      <Title order={4} mb="md" c="var(--text-primary)">
        Campos de Formulário
      </Title>
      <SimpleGrid cols={{ base: 1, sm: 2, lg: 3 }} spacing="lg" mb="xl">
        {COMPONENT_META.filter((m) => m.category === 'input').map((meta) => (
          <ComponentCard key={meta.type} meta={meta} />
        ))}
      </SimpleGrid>

      {/* Special / internal components */}
      <Title order={4} mb="md" c="var(--text-primary)">
        Componentes Especiais &amp; Internos
      </Title>
      <SimpleGrid cols={{ base: 1, sm: 2, lg: 3 }} spacing="lg" mb="xl">
        {COMPONENT_META.filter((m) => m.category !== 'input').map((meta) => (
          <ComponentCard key={meta.type} meta={meta} />
        ))}
      </SimpleGrid>
    </div>
  );
}
