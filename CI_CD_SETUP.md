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
  - Publicação automática no PyPI usando Trusted Publishers (OIDC)
- **URL do pacote**: https://pypi.org/project/createagents/

---

## 🔧 Configurações Necessárias

### 1. Configurar Trusted Publisher no PyPI (RECOMENDADO)

O PyPI agora suporta **Trusted Publishers** usando OIDC, que é **muito mais seguro** que tokens de API. Este método não requer armazenar secrets no GitHub!

#### Passo 1: Configurar Pending Publisher no PyPI (Para primeira publicação)

1. Acesse https://pypi.org/manage/account/publishing/
2. Faça login na sua conta PyPI
3. Clique em **"Add a new pending publisher"**
4. Preencha os campos **EXATAMENTE** como abaixo:
   - **PyPI Project Name**: `createagents` (deve corresponder ao `name` em `pyproject.toml`)
   - **Owner**: `jor0105` (seu usuário/organização do GitHub)
   - **Repository name**: `Create-Agents-AI` (nome do seu repositório)
   - **Workflow name**: `publish.yml` (nome do arquivo de workflow)
   - **Environment name**: `release` (nome do environment no GitHub Actions)
5. Clique em **"Add"**

> **Importante**: Após a primeira publicação bem-sucedida, o "pending publisher" se tornará um "trusted publisher" permanente.

#### Passo 2: Criar Environment no GitHub (Opcional mas Recomendado)

Para adicionar uma camada extra de segurança:

1. Vá para o repositório no GitHub
2. Settings → Environments
3. Clique em **"New environment"**
4. Nome: `release`
5. (Opcional) Configure regras de proteção:
   - ✅ Required reviewers (ex: você mesmo)
   - ✅ Wait timer (ex: 5 minutos)
6. Clique em **"Configure environment"**

> **Nota**: O environment não é obrigatório, mas adiciona proteção contra publicações acidentais.

### Alternativa: Usar Token de API (Método Antigo - NÃO RECOMENDADO)

<details>
<summary>Clique para ver instruções do método antigo (apenas se você não quiser usar Trusted Publishers)</summary>

Se por algum motivo você preferir usar o método antigo com tokens:

1. Acesse https://pypi.org/manage/account/token/
2. Crie um token com escopo de **conta inteira** (para primeira publicação)
3. Adicione como secret `PYPI_API_TOKEN` no GitHub
4. Modifique o workflow para usar `poetry publish` com o token

**⚠️ Aviso**: Este método é menos seguro e não é mais recomendado pelo PyPI.

</details>

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
2. ⏳ **Configurar Trusted Publisher no PyPI** (você precisa fazer - veja seção acima)
3. ⏳ **(Opcional) Criar environment `release` no GitHub** (recomendado para segurança extra)
4. ⏳ **Habilitar GitHub Pages** (você precisa fazer)
5. ⏳ Fazer commit e push dos workflows
6. ⏳ Testar CI com um PR
7. ⏳ Testar deploy da documentação (push para main)
8. ⏳ Criar primeira release para testar publicação no PyPI

---

## 📝 Notas Importantes

- **Testes de integração**: Estão marcados com `@pytest.mark.integration` e são automaticamente excluídos do CI
- **Testes lentos**: Marcados com `@pytest.mark.slow` também são excluídos
- **Coverage mínimo**: 70% (configurado em `pytest.ini` e no workflow)
- **Versionamento**: Sempre atualize `pyproject.toml` antes de criar uma release
- **Documentação**: Atualiza automaticamente a cada push para `main`
- **PyPI**: Publica automaticamente quando você cria uma release no GitHub usando **Trusted Publishers** (OIDC)
- **Segurança**: Não é necessário armazenar tokens do PyPI no GitHub (método moderno e mais seguro)

---

## 🔍 Troubleshooting

### Erro: "Trusted Publisher authentication failed"

- Verifique se o Pending Publisher foi configurado corretamente no PyPI
- Confirme que os campos estão **exatamente** como especificado:
  - Owner: `jor0105`
  - Repository: `Create-Agents-AI`
  - Workflow: `publish.yml`
  - Environment: `release`
- Certifique-se de que o workflow tem `id-token: write` nas permissões

### Erro: "Environment protection rules not satisfied"

- Se você configurou regras de proteção no environment `release`:
  - Aprove a publicação manualmente em Actions
  - Ou aguarde o timer configurado
- Você pode remover o environment do workflow se não quiser essa proteção

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

### Alternativa: Usar método antigo com token

Se o Trusted Publisher não funcionar, você pode voltar para o método antigo:

1. Remova a seção `environment` do `publish.yml`
2. Remova `id-token: write` das permissões
3. Substitua o step de publicação por:
   ```yaml
   - name: Publish to PyPI
     env:
       POETRY_PYPI_TOKEN_PYPI: ${{ secrets.PYPI_API_TOKEN }}
     run: poetry publish --no-interaction
   ```
4. Configure o secret `PYPI_API_TOKEN` no GitHub
