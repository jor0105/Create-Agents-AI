# 🚀 Guia Rápido: Publicar CreateAgents no PyPI

## ✅ Método Recomendado: Trusted Publishers (2024)

Este é o método **mais seguro e moderno** para publicar no PyPI. Não requer tokens de API!

---

## 📋 Passo a Passo (PRIMEIRA PUBLICAÇÃO)

### 1️⃣ Configurar Pending Publisher no PyPI

Acesse: https://pypi.org/manage/account/publishing/

Clique em **"Add a new pending publisher"** e preencha:

```
PyPI Project Name:    createagents
Owner:                jor0105
Repository name:      Create-Agents-AI
Workflow name:        publish.yml
Environment name:     release
```

> ⚠️ **IMPORTANTE**: Os valores devem ser **EXATAMENTE** como acima!

Clique em **"Add"**.

---

### 2️⃣ (Opcional) Criar Environment no GitHub

Acesse: https://github.com/jor0105/Create-Agents-AI/settings/environments

1. Clique em **"New environment"**
2. Nome: `release`
3. (Opcional) Configure proteções:
   - ✅ Required reviewers
   - ✅ Wait timer (5 min)
4. Salve

> 💡 **Dica**: Isso adiciona uma camada de segurança, exigindo aprovação manual antes de publicar.

---

### 3️⃣ Habilitar GitHub Pages

Acesse: https://github.com/jor0105/Create-Agents-AI/settings/pages

1. **Source**: Deploy from a branch
2. **Branch**: `gh-pages` / `root`
3. Clique em **"Save"**

> 📝 **Nota**: O branch `gh-pages` será criado automaticamente no primeiro deploy.

---

### 4️⃣ Fazer Commit dos Workflows

```bash
cd /home/jordan/Programação/CreateAgentsAI
git add .github/workflows/*.yml CI_CD_SETUP.md WORKFLOWS.md
git commit -m "ci: add complete CI/CD with Trusted Publishers"
git push origin main
```

---

### 5️⃣ Verificar que o CI passou

Acesse: https://github.com/jor0105/Create-Agents-AI/actions

Aguarde o workflow **"CI - Quality & Tests"** completar com sucesso ✅

---

### 6️⃣ Publicar Primeira Versão

#### a) Atualizar versão (se necessário)

Edite `pyproject.toml`:

```toml
[project]
name = "createagents"
version = "0.1.0"  # Confirme a versão
```

#### b) Criar Tag e Release

```bash
# Criar tag
git tag v0.1.0
git push origin v0.1.0

# Ou criar tag e release no GitHub:
# https://github.com/jor0105/Create-Agents-AI/releases/new
```

No GitHub:

1. Vá em **Releases** → **"Create a new release"**
2. Tag: `v0.1.0`
3. Título: `v0.1.0 - Initial Release`
4. Descrição: Adicione as mudanças principais
5. Clique em **"Publish release"**

#### c) Aguardar Publicação

O workflow **"CD - Publish to PyPI"** será acionado automaticamente!

Acompanhe em: https://github.com/jor0105/Create-Agents-AI/actions

---

## ✅ Verificação Final

Após a publicação, seu pacote estará disponível em:

- **PyPI**: https://pypi.org/project/createagents/
- **Docs**: https://jor0105.github.io/Create-Agents-AI/

Teste a instalação:

```bash
pip install createagents
```

---

## 🎯 Resumo Visual

```
┌─────────────────────────────────────────────────────────────┐
│  1. PyPI: Configurar Pending Publisher                      │
│     ↓                                                        │
│  2. GitHub: (Opcional) Criar Environment "release"          │
│     ↓                                                        │
│  3. GitHub: Habilitar GitHub Pages                          │
│     ↓                                                        │
│  4. Git: Commit e push dos workflows                        │
│     ↓                                                        │
│  5. GitHub Actions: Verificar CI passou                     │
│     ↓                                                        │
│  6. GitHub: Criar Release (tag v0.1.0)                      │
│     ↓                                                        │
│  7. GitHub Actions: Publicação automática!                  │
│     ↓                                                        │
│  ✅ Pacote publicado no PyPI!                               │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔐 Por que Trusted Publishers é Melhor?

| Aspecto                 | Trusted Publishers (OIDC)      | API Tokens (antigo)      |
| ----------------------- | ------------------------------ | ------------------------ |
| **Segurança**           | ✅ Tokens temporários (15 min) | ❌ Tokens permanentes    |
| **Configuração**        | ✅ Sem secrets no GitHub       | ❌ Requer secret storage |
| **Auditoria**           | ✅ Rastreável ao workflow      | ⚠️ Menos rastreável      |
| **Revogação**           | ✅ Automática                  | ❌ Manual                |
| **Recomendado em 2024** | ✅ SIM                         | ❌ NÃO                   |

---

## ❓ FAQ

### O ambiente "release" é obrigatório?

Não! Você pode remover a seção `environment` do `publish.yml` se preferir. Mas é recomendado para adicionar uma camada de proteção.

### Preciso criar o projeto no PyPI antes?

Não! O "Pending Publisher" reserva o nome automaticamente. A primeira publicação bem-sucedida criará o projeto.

### E se eu já tiver um token configurado?

Você pode continuar usando tokens, mas Trusted Publishers é mais seguro. Veja a seção "Alternativa" no `CI_CD_SETUP.md`.

### Como publicar versões futuras?

Simplesmente:

1. Atualize a versão em `pyproject.toml`
2. Commit e push
3. Crie uma nova tag/release
4. O workflow publicará automaticamente!

---

## 📚 Documentação Adicional

- **PyPI Trusted Publishers**: https://docs.pypi.org/trusted-publishers/
- **GitHub OIDC**: https://docs.github.com/en/actions/deployment/security-hardening-your-deployments/about-security-hardening-with-openid-connect
- **Poetry Publishing**: https://python-poetry.org/docs/libraries/#publishing-to-pypi

---

## 🆘 Precisa de Ajuda?

Consulte:

- `CI_CD_SETUP.md` - Guia completo de configuração
- `WORKFLOWS.md` - Visão geral dos workflows
- Seção "Troubleshooting" em `CI_CD_SETUP.md`
