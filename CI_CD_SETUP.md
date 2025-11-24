# Configuração Final do CI/CD - CreateAgents

## ✅ Workflows Implementados

Três workflows de GitHub Actions foram criados e configurados:

### 1. **CI - Quality & Tests** (`pipeline.yml`)

- **Trigger**: Push para `main` ou `develop`, Pull Requests
- **Executa**:
  - Lint e formatação (pre-commit)
  - Type checking (mypy)
  - Security check (bandit)
  - Testes unitários (excluindo integration e slow tests)
  - Coverage report (mínimo 70%)
- **Versões Python**: 3.12, 3.13, 3.14

### 2. **CD - Deploy Documentation** (`docs.yml`)

- **Trigger**: Push para `main`
- **Executa**:
  - Build da documentação mkdocs
  - Deploy automático para GitHub Pages
- **URL da documentação**: https://jor0105.github.io/Create-Agents-AI/

### 3. **CD - Publish to PyPI** (`publish.yml`)

- **Trigger**: Criação de releases no GitHub
- **Executa**:
  - Build do pacote Python
  - Verificação com twine
  - Publicação automática no PyPI
- **URL do pacote**: https://pypi.org/project/createagents/

---

## 🔧 Configurações Necessárias

### 1. Configurar Token do PyPI

Para que a publicação automática funcione, você precisa configurar o token do PyPI:

#### Passo 1: Criar Token no PyPI

1. Acesse https://pypi.org/manage/account/token/
2. Faça login na sua conta PyPI
3. Clique em "Add API token"
4. Nome do token: `createagents-github-actions`
5. Escopo: **Projeto específico** → selecione `createagents` (após primeira publicação manual) OU **Conta inteira** (para primeira publicação)
6. Clique em "Add token"
7. **COPIE O TOKEN** (você só verá uma vez!)

#### Passo 2: Adicionar Token ao GitHub

1. Vá para o repositório no GitHub
2. Settings → Secrets and variables → Actions
3. Clique em "New repository secret"
4. Nome: `PYPI_API_TOKEN`
5. Value: Cole o token copiado do PyPI
6. Clique em "Add secret"

### 2. Habilitar GitHub Pages

1. Vá para Settings → Pages
2. Em "Source", selecione: **Deploy from a branch**
3. Em "Branch", selecione: `gh-pages` e `/root`
4. Clique em "Save"

> **Nota**: O branch `gh-pages` será criado automaticamente no primeiro deploy da documentação.

---

## 📦 Como Publicar uma Nova Versão

### Processo Completo

1. **Atualizar versão no `pyproject.toml`**:

   ```toml
   [project]
   name = "createagents"
   version = "0.2.0"  # Atualize aqui
   ```

2. **Commit e push das mudanças**:

   ```bash
   git add pyproject.toml
   git commit -m "chore: bump version to 0.2.0"
   git push origin main
   ```

3. **Criar tag da versão**:

   ```bash
   git tag v0.2.0
   git push origin v0.2.0
   ```

4. **Criar Release no GitHub**:

   - Vá para o repositório no GitHub
   - Clique em "Releases" → "Create a new release"
   - Escolha a tag `v0.2.0`
   - Título: `v0.2.0` ou `Release 0.2.0`
   - Descrição: Adicione changelog das mudanças
   - Clique em "Publish release"

5. **Aguardar publicação automática**:
   - O workflow `CD - Publish to PyPI` será acionado automaticamente
   - Acompanhe em: Actions → CD - Publish to PyPI
   - Após conclusão, o pacote estará disponível no PyPI

---

## ✅ Verificação Local

Todos os comandos foram testados localmente e estão funcionando:

### Testes (sem integration)

```bash
poetry run pytest -m "not integration and not slow" --cov=src --cov-report=term-missing
```

**Resultado**: ✅ 1426 passed, 30 skipped, 185 deselected

### Build da Documentação

```bash
poetry run mkdocs build --strict
```

**Resultado**: ✅ Documentation built successfully

### Build do Pacote

```bash
poetry build
```

**Resultado**: ✅ Built createagents-0.1.0.tar.gz and .whl

### Verificação do Pacote

```bash
twine check dist/*
```

**Resultado**: ✅ Package verification passed

---

## 🚀 Próximos Passos

1. ✅ Workflows criados e testados
2. ⏳ **Configurar token `PYPI_API_TOKEN` no GitHub** (você precisa fazer)
3. ⏳ **Habilitar GitHub Pages** (você precisa fazer)
4. ⏳ Fazer commit e push dos workflows
5. ⏳ Testar CI com um PR
6. ⏳ Testar deploy da documentação (push para main)
7. ⏳ Criar primeira release para testar publicação no PyPI

---

## 📝 Notas Importantes

- **Testes de integração**: Estão marcados com `@pytest.mark.integration` e são automaticamente excluídos do CI
- **Testes lentos**: Marcados com `@pytest.mark.slow` também são excluídos
- **Coverage mínimo**: 70% (configurado em `pytest.ini` e no workflow)
- **Versionamento**: Sempre atualize `pyproject.toml` antes de criar uma release
- **Documentação**: Atualiza automaticamente a cada push para `main`
- **PyPI**: Publica automaticamente quando você cria uma release no GitHub

---

## 🔍 Troubleshooting

### Erro: "PYPI_API_TOKEN not found"

- Verifique se o secret foi adicionado corretamente no GitHub
- Nome deve ser exatamente `PYPI_API_TOKEN`

### Erro: "Package already exists on PyPI"

- Você não pode republicar a mesma versão
- Atualize a versão em `pyproject.toml` antes de criar nova release

### GitHub Pages não está funcionando

- Verifique se o branch `gh-pages` foi criado
- Verifique as configurações em Settings → Pages
- Aguarde alguns minutos após o primeiro deploy

### CI falha nos testes

- Execute localmente: `poetry run pytest -m "not integration and not slow"`
- Verifique se todas as dependências estão no `pyproject.toml`
- Verifique se o coverage está acima de 70%
