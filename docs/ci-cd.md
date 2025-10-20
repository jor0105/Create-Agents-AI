# 🔄 CI/CD e Workflows

Este documento descreve os workflows automatizados do projeto e como utilizá-los.

## 📋 Workflows Disponíveis

### 1. Quality Checks (CI)

**Arquivo:** `.github/workflows/ci.yml`

**Quando executa:**

- Push para branches `develop` ou `main`
- Pull requests para `develop` ou `main`
- Manualmente via workflow_dispatch

**O que faz:**

#### 🔍 Lint & Format

- **Black**: Formatação automática de código (88 caracteres por linha)
- **Ruff**: Linting rápido e moderno
- **isort**: Organização de imports
- **Pre-commit**: Executa todos os hooks configurados

#### 🔐 Type Checking & Security

- **mypy**: Verificação de tipos estáticos
- **bandit**: Análise de segurança do código

#### 🧪 Tests & Coverage

- Testes unitários (exclui testes de integração e lentos)
- Cobertura de código mínima: **70%**
- Gera relatório XML de cobertura
- Upload para Codecov (opcional)

#### 🐍 Matrix de Python

Testa em múltiplas versões:

- Python 3.12
- Python 3.13
- Python 3.14

**Exemplo de uso:**

```bash
# Executar localmente os mesmos checks do CI
poetry run pre-commit run --all-files
poetry run mypy src --ignore-missing-imports
poetry run bandit -r src -ll -q
poetry run pytest -m "not integration and not slow" --cov=src --cov-fail-under=70
```

---

### 2. Documentation Build

**Arquivo:** `.github/workflows/docs.yml`

**Quando executa:**

- Manualmente via workflow_dispatch (aba Actions no GitHub)

**O que faz:**

- Instala dependências com Poetry
- Build da documentação com MkDocs
- Valida links e estrutura
- Upload do site gerado como artifact

**Acesso ao artifact:**

1. Vá para a aba **Actions** no GitHub
2. Clique no workflow "Documentation Build"
3. Baixe o artifact `documentation-site`
4. Descompacte e abra `index.html`

**Build local:**

```bash
# Servir docs localmente
poetry run mkdocs serve

# Build para produção
poetry run mkdocs build
```

---

## 🚀 Como Usar os Workflows

### Verificar Status

1. Acesse: `https://github.com/jor0105/AI_Agent/actions`
2. Veja os workflows recentes e seus status
3. Clique em um workflow para ver detalhes

### Executar Manualmente

#### Documentation Build:

1. Vá para **Actions** → **Documentation Build**
2. Clique em "Run workflow"
3. Selecione a branch
4. Clique em "Run workflow"

### Badges (Opcional)

Adicione ao README.md:

```markdown
[![Quality Checks](https://github.com/jor0105/AI_Agent/workflows/Quality%20Checks/badge.svg)](https://github.com/jor0105/AI_Agent/actions)
[![codecov](https://codecov.io/gh/jor0105/AI_Agent/branch/develop/graph/badge.svg)](https://codecov.io/gh/jor0105/AI_Agent)
```

---

## 🔧 Configuração Local

### Pre-commit Hooks

Os mesmos checks do CI são executados localmente antes de cada commit:

```bash
# Instalar hooks
poetry run pre-commit install

# Executar manualmente
poetry run pre-commit run --all-files

# Pular hooks (não recomendado)
git commit --no-verify
```

### Estrutura dos Hooks

| Hook                | Descrição                         | Ferramenta |
| ------------------- | --------------------------------- | ---------- |
| trailing-whitespace | Remove espaços em branco no final | pre-commit |
| end-of-files        | Garante EOF no final dos arquivos | pre-commit |
| check-yaml          | Valida sintaxe YAML               | pre-commit |
| check-json          | Valida sintaxe JSON               | pre-commit |
| check-toml          | Valida sintaxe TOML               | pre-commit |
| black               | Formatação de código              | Black      |
| ruff                | Linting moderno                   | Ruff       |
| ruff-format         | Formatação com Ruff               | Ruff       |
| isort               | Organização de imports            | isort      |
| mypy                | Type checking                     | mypy       |
| pydocstyle          | Validação de docstrings           | pydocstyle |
| yamllint            | Linting de YAML                   | yamllint   |

---

## 📊 Métricas e Cobertura

### Cobertura de Código

**O que é:** Porcentagem de código executada pelos testes.

**Mínimo exigido:** 70%

**Como verificar:**

```bash
# Executar testes com cobertura
poetry run pytest --cov=src --cov-report=term-missing

# Gerar relatório HTML
poetry run pytest --cov=src --cov-report=html
# Abrir: htmlcov/index.html
```

**Exemplo de saída:**

```
Name                                    Stmts   Miss  Cover   Missing
---------------------------------------------------------------------
src/domain/entities/agent_domain.py        45      3    93%   78-80
src/application/use_cases/chat.py          32      0   100%
src/infra/adapters/ollama.py               67     10    85%   45-52, 89
---------------------------------------------------------------------
TOTAL                                     892    125    86%
```

### Interpretar Relatório

- **Stmts**: Total de linhas de código
- **Miss**: Linhas não executadas pelos testes
- **Cover**: Porcentagem de cobertura
- **Missing**: Números das linhas não cobertas

---

## 🐛 Troubleshooting

### CI falhou - O que fazer?

#### 1. Pre-commit falhou

```bash
# Executar localmente
poetry run pre-commit run --all-files

# Corrigir automaticamente
poetry run black src tests
poetry run isort src tests
```

#### 2. Testes falham

```bash
# Executar localmente com verbose
poetry run pytest -v

# Executar teste específico
poetry run pytest tests/path/to/test.py::TestClass::test_method
```

#### 3. Type checking (mypy) falhou

```bash
# Executar localmente
poetry run mypy src --ignore-missing-imports --pretty

# Adicionar type hints ausentes
def func(x: int) -> str:
    return str(x)
```

#### 4. Cobertura < 70%

```bash
# Ver quais linhas não estão cobertas
poetry run pytest --cov=src --cov-report=term-missing

# Adicionar testes para as linhas faltantes
```

#### 5. Security check (bandit) falhou

```bash
# Executar localmente
poetry run bandit -r src -ll -q

# Ver detalhes
poetry run bandit -r src -ll
```

---

## 📦 Cache de Dependências

Os workflows usam cache para acelerar builds:

**O que é cacheado:**

- Ambiente virtual Python (`.venv`)
- Dependências do Poetry

**Como limpar cache no GitHub:**

1. Vá para **Settings** → **Actions** → **Caches**
2. Delete caches antigos

**Key do cache:**

```
venv-{OS}-{Python-Version}-{poetry.lock-hash}
```

---

## 🔐 Segurança

### Secrets no GitHub

Configure em **Settings** → **Secrets and variables** → **Actions**:

| Secret           | Descrição        | Obrigatório       |
| ---------------- | ---------------- | ----------------- |
| `OPENAI_API_KEY` | Chave da OpenAI  | Não (para testes) |
| `CODECOV_TOKEN`  | Token do Codecov | Não (público)     |

### Permissões dos Workflows

Ambos workflows têm apenas permissão de **leitura**:

```yaml
permissions:
  contents: read
```

---

## 🎯 Boas Práticas

### Antes de Fazer Push

```bash
# 1. Executar pre-commit
poetry run pre-commit run --all-files

# 2. Executar testes
poetry run pytest

# 3. Verificar cobertura
poetry run pytest --cov=src --cov-fail-under=70

# 4. Type checking
poetry run mypy src --ignore-missing-imports
```

### Ao Criar PR

1. ✅ Todos os checks do CI devem passar
2. ✅ Adicionar descrição clara do que mudou
3. ✅ Referenciar issues relacionadas
4. ✅ Atualizar documentação se necessário

### Commits

Use **Conventional Commits**:

- `feat:` Nova funcionalidade
- `fix:` Correção de bug
- `docs:` Mudança apenas na documentação
- `style:` Formatação, sem mudança de código
- `refactor:` Refatoração
- `test:` Adicionar ou modificar testes
- `chore:` Manutenção geral

**Exemplos:**

```bash
git commit -m "feat: add support for Claude AI provider"
git commit -m "fix: handle None response from Ollama API"
git commit -m "docs: update CI/CD workflow documentation"
```

---

## 📚 Referências

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Poetry Documentation](https://python-poetry.org/docs/)
- [Pre-commit Hooks](https://pre-commit.com/)
- [pytest Coverage](https://pytest-cov.readthedocs.io/)
- [Conventional Commits](https://www.conventionalcommits.org/)

---

**Última atualização:** Outubro 2025
