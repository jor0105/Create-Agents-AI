# Guia de Instalação do Usuário

> Siga este passo a passo para instalar e configurar o **Create Agents AI** com segurança e confiabilidade no seu ambiente.

---

## 📝 Pré-requisitos

- **Python 3.12+** ([Download](https://www.python.org/downloads/))
- **pip** (geralmente incluído com Python)

> **Dica:** Recomenda-se usar ambientes virtuais para isolar as dependências do projeto.

---

## ⚡ Instalação Rápida

### 1. Criar Ambiente Virtual (Recomendado)

```bash
# Criar ambiente virtual
python3 -m venv .venv

# Ativar ambiente virtual
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate  # Windows
```

### 2. Instalar via PyPI

```bash
# Instalação básica
pip install createagents

# OU com suporte a arquivos (PDF, Excel, CSV, Parquet)
pip install createagents[file-tools]
```

> **Nota:** A opção `[file-tools]` adiciona suporte para leitura de arquivos PDF, Excel, CSV e Parquet.

---

### 3. Configurar Variáveis de Ambiente

```bash
cp .env.example .env
# Edite o arquivo .env e adicione sua chave OPENAI_API_KEY
```

Exemplo de configuração:

```env
OPENAI_API_KEY=sk-proj-sua-chave
# Adicione outras variáveis se necessário
```

---

### 4. Testar Instalação

```python
import asyncio
from createagents import CreateAgent

async def main():
    agent = CreateAgent(
        provider="openai",
        model="gpt-4",
        instructions="Você é um assistente útil."
    )
    response = await agent.chat("Olá! Teste de instalação.")
    print(response)

asyncio.run(main())
```

Se o código acima rodar sem erros, a instalação está concluída!

---

## 🔑 Configuração OpenAI

1. Crie uma conta em [platform.openai.com](https://platform.openai.com)
1. Gere uma nova API Key em **API Keys**
1. Adicione ao arquivo `.env`:

```env
OPENAI_API_KEY=sk-proj-sua-chave
```

> **Atenção:** Nunca compartilhe sua chave em repositórios públicos.

---

## 🤖 Configuração Ollama (Opcional)

Permite rodar modelos de IA **localmente** (privacidade total, sem custos de API).

### Instalar Ollama

**Linux:**

```bash
curl -fsSL https://ollama.ai/install.sh | sh
```

**macOS:**

```bash
brew install ollama
```

**Windows:**

Baixe em: [ollama.ai/download/windows](https://ollama.ai/download/windows)

### Baixar Modelos

```bash
ollama pull llama3.2:latest     # Modelo recomendado
ollama pull granite4:latest     # Alternativo
ollama list             # Ver modelos disponíveis
```

### Usar no Código

```python
import asyncio
from createagents import CreateAgent

async def main():
    agent = CreateAgent(
        provider="ollama",
        model="llama3.2",
        instructions="Você é um assistente local."
    )
    response = await agent.chat("Explique machine learning")
    print(response)

asyncio.run(main())
```

> **Dica:** Rode `ollama serve` antes de usar para garantir que o servidor está ativo.

---

## 🔒 Segurança e Boas Práticas

- **Nunca** faça commit do arquivo `.env` (já está no `.gitignore`)
- Mantenha suas chaves privadas e rotacione periodicamente
- Use ambientes virtuais para isolar dependências
- Atualize dependências regularmente (`poetry update` ou `pip install -U`)

---

## 🛠️ Solução de Problemas

### Erros Comuns

- **"OPENAI_API_KEY not found"**: Verifique se o arquivo `.env` está na raiz e a variável está correta, sem espaços ou aspas.
- **"ModuleNotFoundError"**: Ative o ambiente virtual e reinstale as dependências.
- **Ollama não conecta**: Rode `ollama serve` e verifique se o modelo está baixado.
- **Problemas de permissão**: Execute comandos com `sudo` apenas se necessário e nunca para instalar dependências Python no sistema global.

### Dicas de Diagnóstico

- Use `poetry run python --version` ou `python --version` para checar a versão ativa.
- Use `poetry show` ou `pip list` para listar dependências instaladas.
- Consulte os logs de erro completos para identificar problemas específicos.

Se persistir, consulte a [FAQ](faq-user.md) ou abra uma issue no [GitHub](https://github.com/jor0105/Create-Agents-AI/issues).

---

## 👨‍💻 Instalação para Desenvolvimento (Contribuidores)

Se você deseja **contribuir** com o projeto ou precisa da versão de desenvolvimento:

### 1. Clonar o Repositório

```bash
git clone https://github.com/jor0105/Create-Agents-AI.git
cd Create-Agents-AI
```

### 2. Instalar com Poetry

```bash
# Instale o Poetry se necessário
curl -sSL https://install.python-poetry.org | python3 -

# Instalação básica
poetry install

# OU com suporte a file-tools
poetry install -E file-tools

# Ativar ambiente virtual
poetry shell
```

### 3. Configurar Ambiente de Desenvolvimento

```bash
# Copiar arquivo de exemplo
cp .env.example .env

# Editar e adicionar sua chave
# OPENAI_API_KEY=sk-proj-sua-chave
```

### 4. Instalar Pre-commit Hooks

```bash
# Instalar hooks de qualidade de código
poetry run pre-commit install

# Executar checks manualmente
poetry run pre-commit run --all-files
```

📖 **Mais informações:** [Guia de Contribuição](../dev-guide/contribute.md)

---

## 🚀 Próximos Passos

- [Uso Básico](basic-usage-user.md)
- [Exemplos](examples-user.md)
- [FAQ](faq-user.md)
- [Referência de Ferramentas](../reference/tools.md)
- [API Reference](../reference/api.md)

---

**Versão:** 0.2.0 | **Atualização:** 02/12/2025
