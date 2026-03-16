# Field Schema Reference — `@erp-dsl/form-ui`

Documentação de referência para todos os campos de formulário suportados pelo DSL Engine.
Voltada para: **LLMs** (geração de schemas), **usuários** (configuração de formulários) e **suporte** (diagnóstico).

---

## Propriedades Comuns

Todas as props abaixo existem em **todos** os tipos de campo:

| Prop          | Tipo                  | Padrão  | Descrição                                                        |
|---------------|-----------------------|---------|------------------------------------------------------------------|
| `id`          | `string`              | —       | **Obrigatório.** Identificador único do campo no formulário      |
| `type`        | `string`              | —       | **Obrigatório.** Tipo do componente (ver tabela abaixo)          |
| `label`       | `string`              | —       | Rótulo exibido acima do campo                                    |
| `placeholder` | `string`              | = label | Texto de placeholder do input                                    |
| `required`    | `boolean`             | —       | `true` → badge vermelho "Obrigatório" + validação no submit; `false` → badge cinza "Opcional"; omitido → sem badge |
| `description` | `string`              | —       | Texto de ajuda exibido abaixo do campo (hint)                    |
| `readonly`    | `boolean`             | `false` | Campo somente leitura                                            |
| `condition`   | `FieldCondition`      | —       | Condição de visibilidade (ver seção Condições)                   |

---

## Propriedades de Validação

| Prop         | Tipo                | Aplicável a             | Descrição                                           |
|--------------|---------------------|-------------------------|-----------------------------------------------------|
| `maxLength`  | `number`            | `text`, `textarea`      | Limite de caracteres → habilita o char counter UX   |
| `minLength`  | `number`            | `text`, `textarea`      | Mínimo de caracteres (validado no submit)            |
| `min`        | `number`            | `number`, `money`       | Valor mínimo numérico permitido                     |
| `max`        | `number`            | `number`, `money`       | Valor máximo numérico permitido                     |
| `validation` | `ValidationRule[]`  | todos texto             | Regras extras com `pattern` (regex) e `message`     |

### `ValidationRule`

```ts
{
  pattern?: string;  // Regex como string, ex: "^[A-Z]{2}\\d{6}$"
  message?: string;  // Mensagem de erro customizada (PT-BR)
}
```

---

## Tipos de Campo

### `text` — Texto Simples

```json
{
  "id": "nome",
  "type": "text",
  "label": "Nome completo",
  "placeholder": "Ex: João da Silva",
  "required": true,
  "maxLength": 100,
  "minLength": 3,
  "description": "Use o nome como no documento oficial"
}
```

**UX**: char counter `0/100`, ícone ✓ verde após preencher, badge "Obrigatório".

---

### `textarea` — Texto Multilinha

```json
{
  "id": "obs",
  "type": "textarea",
  "label": "Observações",
  "required": false,
  "maxLength": 500,
  "description": "Informações complementares para o pedido"
}
```

**UX**: char counter `0/500`, auto-resize (min 3 linhas, max 8), badge "Opcional".

---

### `number` — Número

```json
{
  "id": "quantidade",
  "type": "number",
  "label": "Quantidade",
  "required": true,
  "min": 1,
  "max": 9999,
  "description": "Número inteiro entre 1 e 9999"
}
```

**UX**: separadores no padrão BR (`.` milhar, `,` decimal), ícone de status.

---

### `money` — Moeda (BRL)

```json
{
  "id": "preco",
  "type": "money",
  "label": "Preço de venda",
  "required": true,
  "min": 0.01,
  "description": "Valor em R$ com 2 casas decimais"
}
```

**UX**: prefixo `R$`, 2 casas decimais fixas, separadores BR.

---

### `select` — Seleção

```json
{
  "id": "categoria",
  "type": "select",
  "label": "Categoria",
  "required": true,
  "options": [
    { "value": "A", "label": "Categoria A" },
    { "value": "B", "label": "Categoria B" }
  ]
}
```

Com fonte dinâmica:
```json
{
  "id": "modelo",
  "type": "select",
  "label": "Modelo de IA",
  "required": true,
  "dataSource": "/api/llm/models",
  "dataSourceParams": { "provider": "provider_id" }
}
```

**UX**: pesquisa (searchable), clearable, ícone ✓ após seleção.

---

### `date` — Data

```json
{
  "id": "data_nascimento",
  "type": "date",
  "label": "Data de nascimento",
  "required": true,
  "description": "Formato: DD/MM/AAAA"
}
```

**Formato de valor**: `YYYY-MM-DD` (ISO 8601).

---

### `datetime` — Data e Hora

```json
{
  "id": "agendamento",
  "type": "datetime",
  "label": "Data e hora do agendamento",
  "required": false
}
```

**Formato de valor**: `YYYY-MM-DDTHH:mm` (ISO 8601 local).

---

### `checkbox` — Caixa de Seleção

```json
{
  "id": "aceite_termos",
  "type": "checkbox",
  "label": "Aceito os Termos de Uso",
  "required": true,
  "description": "Leia os termos antes de aceitar"
}
```

**UX**: asterisco `*` vermelho no label quando `required`.

---

### `switch` — Toggle Booleano

```json
{
  "id": "ativo",
  "type": "switch",
  "label": "Ativo no sistema",
  "required": false,
  "description": "Desativar oculta o registro das listagens"
}
```

**UX**: layout horizontal com borda, badge no label.

---

### `segmented` — Seleção Segmentada

```json
{
  "id": "modalidade",
  "type": "segmented",
  "label": "Modalidade",
  "required": true,
  "options": [
    { "value": "presencial", "label": "Presencial" },
    { "value": "online", "label": "Online" },
    { "value": "hibrido", "label": "Híbrido" }
  ]
}
```

---

## Tipos de Layout (Containers)

Containers **não geram campos** no formulário — apenas organizam os campos filhos.

### `section` — Seção com Título

```json
{
  "id": "sec_dados",
  "type": "section",
  "label": "Dados Pessoais",
  "columns": 2,
  "components": [
    { "id": "nome", "type": "text", "label": "Nome" },
    { "id": "cpf", "type": "text", "label": "CPF" }
  ]
}
```

### `grid` — Grid de Colunas

```json
{
  "id": "grid_preco",
  "type": "grid",
  "columns": 3,
  "components": [
    { "id": "custo", "type": "money", "label": "Custo" },
    { "id": "preco", "type": "money", "label": "Preço" },
    { "id": "markup", "type": "number", "label": "Markup %", "readonly": true, "computed": { "formula": "markup", "deps": ["preco", "custo"] } }
  ]
}
```

### `tabs` — Abas

```json
{
  "id": "tabs_principal",
  "type": "tabs",
  "components": [
    {
      "id": "tab_geral",
      "type": "tab",
      "label": "Geral",
      "components": [...]
    },
    {
      "id": "tab_fiscal",
      "type": "tab",
      "label": "Fiscal",
      "components": [...]
    }
  ]
}
```

---

## Condições de Visibilidade

```json
{
  "id": "campo_cpf",
  "type": "text",
  "label": "CPF",
  "condition": {
    "field": "tipo_pessoa",
    "value": "fisica"
  }
}
```

O campo só aparece quando `form.values.tipo_pessoa === "fisica"`.

---

## Campos Computados (Readonly + Fórmula)

```json
{
  "id": "margem",
  "type": "number",
  "label": "Margem %",
  "readonly": true,
  "computed": {
    "formula": "margem",
    "deps": ["preco", "custo"]
  }
}
```

Fórmulas disponíveis: `markup`, `margem`.

---

## Validação com Pattern (Regex)

```json
{
  "id": "cep",
  "type": "text",
  "label": "CEP",
  "required": true,
  "maxLength": 9,
  "validation": [
    {
      "pattern": "^\\d{5}-?\\d{3}$",
      "message": "CEP inválido. Use o formato 00000-000"
    }
  ]
}
```

---

## UX de Status por Estado

| Estado                        | Ícone | Cor     | Condição                                  |
|-------------------------------|-------|---------|-------------------------------------------|
| Idle (inicial)                | —     | —       | Campo não tocado                          |
| Válido                        | ✓     | Verde   | Tocado + tem valor + sem erro             |
| Inválido                      | ✗     | Vermelho| Tem mensagem de erro (do useForm)         |
| Char counter normal           | —     | Dimmed  | < 90% do maxLength                        |
| Char counter alerta           | —     | Amarelo | ≥ 90% do maxLength                        |
| Char counter no limite        | —     | Vermelho| = maxLength                               |

> **Nota para suporte**: o estado "tocado" é controlado pelo evento `onBlur` do input.
> O ícone de status só aparece após o usuário interagir com o campo — não no carregamento inicial.
