# 🔄 CI/CD e Workflows

Workflows automatizados do projeto com GitHub Actions.

---

## 📋 Workflows

### 1. Quality Checks (CI)

**Arquivo:** `.github/workflows/ci.yml`

**Executa:**

- Push/PR para `develop` ou `main`
- Manualmente via workflow_dispatch

**Checks:**

#### 🔍 Lint & Format

- **Black**: Formatação (88 chars/linha)
- **Ruff**: Linting rápido
- **isort**: Organização de imports
- **Pre-commit**: Todos os hooks

#### 🔐 Type Checking & Security

- **mypy**: Verificação de tipos
- **bandit**: Análise de segurança

#### 🧪 Tests & Coverage

- Testes unitários
- Cobertura mínima: **70%**
- Upload para Codecov (opcional)

#### 🐍 Matrix Python

- Python 3.12
- Python 3.13
- Python 3.14

**Executar localmente:**

```bash
poetry run pre-commit run --all-files
poetry run mypy src --ignore-missing-imports
poetry run bandit -r src -ll -q
poetry run pytest --cov=src --cov-fail-under=70
```

---

## Configuração Local

### Pre-commit Hooks

Executa checks antes de cada commit:

```bash
# Instalar
poetry run pre-commit install

# Executar manualmente
poetry run pre-commit run --all-files

# Pular (não recomendado)
git commit --no-verify
```

### Hooks Configurados

| Hook                | Descrição             |
| ------------------- | --------------------- |
| trailing-whitespace | Remove espaços finais |
| end-of-files        | Garante EOF           |
| check-yaml          | Valida YAML           |
| check-json          | Valida JSON           |
| check-toml          | Valida TOML           |
| black               | Formatação            |
| ruff                | Linting               |
| isort               | Organiza imports      |
| mypy                | Type checking         |
| pydocstyle          | Valida docstrings     |

---

## 📊 Cobertura de Código

**Mínimo exigido:** 70%

**Verificar:**

```bash
# Com cobertura
poetry run pytest --cov=src --cov-report=term-missing

# Relatório HTML
poetry run pytest --cov=src --cov-report=html
# Abrir: htmlcov/index.html
```

**Exemplo de saída:**

```
Name                          Stmts   Miss  Cover   Missing
-----------------------------------------------------------
src/domain/entities/agent.py     45      3    93%   78-80
src/application/use_cases.py     32      0   100%
-----------------------------------------------------------
TOTAL                           892    125    86%
```

---

## 🐛 Troubleshooting

### CI Falhou - Ações

#### 1. Pre-commit

```bash
poetry run pre-commit run --all-files
poetry run black src tests
poetry run isort src tests
```

#### 2. Testes

```bash
poetry run pytest -v
```

#### 3. Type Checking

```bash
poetry run mypy src --ignore-missing-imports
```

#### 4. Cobertura < 70%

```bash
poetry run pytest --cov=src --cov-report=term-missing
# Adicionar testes para linhas não cobertas
```

#### 5. Security Check

```bash
poetry run bandit -r src -ll
```

---

## 🎯 Boas Práticas

### Antes de Push

```bash
# 1. Pre-commit
poetry run pre-commit run --all-files

# 2. Testes
poetry run pytest

# 3. Cobertura
poetry run pytest --cov=src --cov-fail-under=70

# 4. Type checking
poetry run mypy src --ignore-missing-imports
```

### Commits

Use **Conventional Commits**:

- `feat:` Nova funcionalidade
- `fix:` Correção de bug
- `docs:` Mudança na documentação
- `style:` Formatação
- `refactor:` Refatoração
- `test:` Adicionar/modificar testes
- `chore:` Manutenção

**Exemplos:**

```bash
git commit -m "feat: add Claude AI provider"
git commit -m "fix: handle None response from API"
git commit -m "docs: update CI/CD guide"
```

---

**Última atualização:** Novembro 2025
