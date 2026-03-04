# AutoSystem Platform — Admin Dashboard

Painel de gestão da plataforma SaaS AutoSystem. Esta é a camada de **marketplace/admin** onde o usuário gerencia sua conta, projetos e aplicativos.

> **Analogia**: Assim como o Vercel Dashboard gerencia deploys, ou o Supabase Dashboard gerencia projetos — este frontend gerencia os aplicativos ERP do AutoSystem.

## Stack

- **React 19** + TypeScript
- **Vite 7** (build tool)
- **Mantine 7** (UI components)
- **Zustand** (state management)
- **React Query** (server state)
- **Axios** (HTTP client)
- **React Router 7** (routing)

## Features

- **Autenticação**: Signup, Login com JWT
- **Planos**: Seleção de plano (Free / Pro)
- **Projetos**: CRUD de projetos com sidebar estilo Supabase
- **Empresa**: Configuração de dados da empresa (PJ/PF)
- **Apps**: Criação de aplicativos com configuração de LLM
- **Database**: Visualização de credenciais do banco isolado

## Architecture

```
src/
  pages/
    Login.tsx              # Tela de login
    SignUp.tsx             # Cadastro de conta
    PlanSelection.tsx      # Seleção de plano
    dashboard/
      Dashboard.tsx        # Lista de projetos + sidebar
      ProjectSettings.tsx  # Orquestrador de tabs do projeto
      CreateAppModal.tsx   # Modal de criação de app
      tabs/
        GeneralTab.tsx     # Info geral do projeto
        CompanyTab.tsx     # Dados da empresa
        AppsTab.tsx        # Lista de apps
        DatabaseTab.tsx    # Conexão do banco
  services/
    api.ts                 # Axios com JWT interceptor
  state/
    authStore.ts           # Zustand: autenticação
    dashboardStore.ts      # Zustand: projetos e apps
```

## Development

```bash
pnpm install
pnpm dev          # http://localhost:5175
```

## Build

```bash
pnpm build        # Output em dist/
```

## Docker

O Dockerfile usa multi-stage build (Node → Nginx). Em produção, as requisições `/api/*` são proxied para o backend via Nginx.
