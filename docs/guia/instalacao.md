# 📦 Guia de Instalação

Configure o **Create Agents AI** em sua máquina.

______________________________________________________________________

## 📋 Pré-requisitos

- **Python 3.12+** ([Download](https://www.python.org/downloads/))
- **Poetry** (recomendado) ou **pip**
- **Git** ([Download](https://git-scm.com/downloads))

______________________________________________________________________

## ⚡ Instalação Rápida

### 1. Clonar o Repositório

```bash
git clone https://github.com/jor0105/Creator-Agents-AI.git
cd Create-Agents-AI
```

### 2. Instalar Dependências

**Com Poetry (recomendado):**

```bash
# Instalar Poetry se necessário
curl -sSL https://install.python-poetry.org | python3 -

# Instalação básica
poetry install

# OU com suporte a arquivos (PDF, Excel, CSV)
poetry install -E file-tools

# Ativar ambiente
poetry shell
```

**Com pip:**

```bash
# Criar ambiente virtual
python3 -m venv .venv
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate  # Windows

# Instalar
pip install -e .
# OU com file-tools
pip install -e ".[file-tools]"
```

### 3. Configurar Variáveis de Ambiente

```bash
# Copiar exemplo
cp .env.example .env

# Editar e adicionar sua chave
# OPENAI_API_KEY=sk-proj-sua-chave
```

### 4. Testar Instalação

```python
from createagents import CreateAgent

agent = CreateAgent(provider="openai", model="gpt-4")
print("✅ Instalação bem-sucedida!")
```

______________________________________________________________________

## 🔐 Configuração OpenAI

### 1. Obter API Key

1. Acesse [platform.openai.com](https://platform.openai.com)
1. Faça login
1. Vá para **API Keys**
1. Crie nova chave

### 2. Configurar .env

```bash
OPENAI_API_KEY=sk-proj-sua-chave
```

### 3. Testar

```python
agent = CreateAgent(provider="openai", model="gpt-4")
response = agent.chat("2+2=?")
print(response)  # Deve responder "4"
```

## 🖥️ Configuração Ollama (Opcional)

Ollama permite executar modelos **localmente** (privacidade total, sem custos).

### 1. Instalar Ollama

**Linux:**

```bash
curl -fsSL https://ollama.ai/install.sh | sh
```

**macOS:**

```bash
brew install ollama
```

**Windows:**
Download: [ollama.ai/download/windows](https://ollama.ai/download/windows)

### 2. Baixar Modelos

```bash
# Recomendado
ollama pull llama2  # 4GB

# Outros
ollama pull mistral  # 4GB
ollama pull codellama  # 7GB
ollama pull gemma  # 2GB

# Ver modelos
ollama list
```

### 3. Usar no código

```python
agent = CreateAgent(provider="ollama", model="llama2")
response = agent.chat("Explique machine learning")
# 100% local, privado, sem custos
```

______________________________________________________________________

## 🛡️ Segurança

⚠️ **Nunca** faça commit do `.env`

- Já está no `.gitignore`
- Mantenha suas API keys privadas
- Rotacione chaves periodicamente

______________________________________________________________________

## 🔧 Solução de Problemas

### "OPENAI_API_KEY not found"

- Verifique se `.env` existe na raiz
- Sem espaços ou aspas na chave

### "ModuleNotFoundError"

- Ative o ambiente virtual
- Reinstale: `poetry install`

### Ollama não conecta

```bash
ollama serve  # Inicie o servidor
ollama list   # Verifique modelos
```

______________________________________________________________________

## 🎯 Próximos Passos

- [Uso Básico](uso-basico.md)
- [Exemplos](exemplos.md)
- [API Reference](../api.md)

______________________________________________________________________

**Versão:** 0.1.0 | **Atualização:** 17/11/2025
