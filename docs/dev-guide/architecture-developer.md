# Guia de Arquitetura para Desenvolvedores

Este documento detalha a arquitetura do Create Agents AI, baseada em Clean Architecture e princípios SOLID.

## Estrutura de Camadas

```
┌───────────────────────────────┐
│        application           │  ← Interface do Usuário (CreateAgent)
│     (Controllers/UI)         │
└──────────────┬───────────────┘
               │
┌──────────────▼───────────────┐
│        APPLICATION           │  ← Use Cases & DTOs
│    (Business Logic)          │
└──────────────┬───────────────┘
               │
┌──────────────▼───────────────┐
│          DOMAIN              │  ← Entities & Rules
│    (Core Business)           │
└──────────────▲───────────────┘
               │
┌──────────────┴───────────────┐
│      INFRASTRUCTURE          │  ← Adapters (OpenAI, Ollama)
│  (External Services)         │
└──────────────────────────────┘
```

### 1. Domain (Domínio)

- Localização: `src/createagents/domain/`
- Responsável por regras de negócio puras, entidades, value objects, exceptions e serviços de domínio.

### 2. Application (Aplicação)

- Localização: `src/createagents/application/`
- Orquestra casos de uso, expõe a fachada `CreateAgent`, define DTOs e interfaces.

### 3. Infrastructure (Infraestrutura)

- Localização: `src/createagents/infra/`
- Implementa integrações externas, adapters, tools, config e factories.

## Princípios SOLID

- **SRP**: Cada classe tem responsabilidade única.
- **OCP**: Extensível sem modificar código existente.
- **LSP**: Adapters são intercambiáveis.
- **ISP**: Interfaces específicas e focadas.
- **DIP**: Depende de abstrações, não implementações.

## Padrões de Design

- Repository, Factory, Facade, Value Object.

## Fluxo de Dados

```
Usuário → CreateAgent.chat()
    → ChatWithAgentUseCase.execute()
        → ChatRepository.chat()
            → OpenAIChatAdapter / OllamaChatAdapter
                → API Externa
            ← Response
        ← ChatOutputDTO
    ← response: str
```

## Benefícios

- Testável, flexível, escalável e manutenível.

## Versão

0.1.0 | Atualização: 17/11/2025
