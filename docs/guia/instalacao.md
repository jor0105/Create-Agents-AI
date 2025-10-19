# Guia de Instalação

Este guia irá ajudá-lo a configurar o ambiente de desenvolvimento do AI Agent Creator em sua máquina local.

---

## Pré-requisitos

Antes de começar, certifique-se de ter instalado:

- **Python 3.10+** ([Download](https://www.python.org/downloads/))
- **pip** (geralmente incluído com Python)
- **Git** ([Download](https://git-scm.com/downloads))
- **Ferramenta de ambiente virtual** (venv, recomendado)

---

## Instalação Passo a Passo

### 1. Clonar o Repositório

\`\`\`bash
git clone https://github.com/jor0105/AI_Agent.git
cd AI_Agent
\`\`\`

### 2. Criar um Ambiente Virtual

Criar um ambiente virtual isola as dependências do projeto da instalação Python do sistema.

**No Linux/macOS:**

\`\`\`bash
python3 -m venv venv
source venv/bin/activate
\`\`\`

**No Windows:**

\`\`\`bash
python -m venv venv
venv\Scripts\activate
\`\`\`

Você deve ver \`(venv)\` no prompt do terminal, indicando que o ambiente virtual está ativo.

### 3. Instalar Dependências

Instale todos os pacotes necessários usando pip:

\`\`\`bash
pip install --upgrade pip
pip install -r requirements.txt
\`\`\`

Alternativamente, se preferir usar Poetry:

\`\`\`bash
pip install poetry
poetry install
\`\`\`

### 4. Configurar Variáveis de Ambiente

Crie um arquivo \`.env\` no diretório raiz do projeto:

\`\`\`bash
cp .env.example .env  # ou crie o arquivo manualmente
\`\`\`

Edite o arquivo \`.env\` e adicione suas credenciais de API:

\`\`\`bash
# Configuração OpenAI
OPENAI_API_KEY=sk-proj-sua-chave-api-aqui

# Opcional: Adicione outras configurações
# LOG_LEVEL=INFO
# MAX_RETRIES=3
\`\`\`

!!! warning "Aviso de Segurança"
    Nunca faça commit do seu arquivo \`.env\` para controle de versão. Ele já está no \`.gitignore\` para prevenir commits acidentais.

### 5. Verificar Instalação

Execute este teste rápido para garantir que tudo está configurado corretamente:

\`\`\`python
from src import AIAgent

# Testar funcionalidade básica
agent = AIAgent(
    model="gpt-4",
    name="Agente de Teste",
    instructions="Você é um assistente útil."
)

print("✅ Instalação bem-sucedida!")
print(f"Agente '{agent.get_configs()['name']}' criado com sucesso")
\`\`\`

---

## Configuração Específica por Provedor

### Configuração OpenAI

1. Acesse [OpenAI Platform](https://platform.openai.com)
2. Cadastre-se ou faça login na sua conta
3. Navegue até a seção **API Keys**
4. Clique em **Create new secret key**
5. Copie a chave e adicione ao seu arquivo \`.env\`

**Modelos Suportados:**

- \`gpt-4\`
- \`gpt-4-turbo\`
- \`gpt-3.5-turbo\`
- E outros modelos OpenAI

### Configuração Ollama (Opcional)

Ollama permite executar modelos de IA localmente para privacidade completa e sem custos de API.

**Instalação:**

**No Linux:**

\`\`\`bash
curl -fsSL https://ollama.ai/install.sh | sh
\`\`\`

**No macOS:**

\`\`\`bash
brew install ollama
\`\`\`

**No Windows:**

Baixe e instale de [ollama.ai](https://ollama.ai)

**Baixar Modelos:**

\`\`\`bash
# Baixar um modelo
ollama pull llama2

# Ou baixar outros modelos
ollama pull mistral
ollama pull codellama
\`\`\`

**Uso:**

\`\`\`python
from src import AIAgent

agent = AIAgent(
    model="llama2",
    name="Assistente Local",
    instructions="Você é um assistente útil.",
    local_ai="ollama"  # Usar provedor Ollama
)
\`\`\`

---

## Dependências de Desenvolvimento

Para desenvolvimento e contribuição, instale dependências adicionais de dev:

\`\`\`bash
pip install -r requirements-dev.txt
\`\`\`

Ou com Poetry:

\`\`\`bash
poetry install --with dev
\`\`\`

Isso inclui:

- **pytest** - Framework de testes
- **isort** - Ordenação de imports
- **pre-commit** - Hooks Git para qualidade de código
- **mkdocs** - Gerador de documentação

### Configurando Pre-commit Hooks

\`\`\`bash
pre-commit install
\`\`\`

Isso verificará automaticamente seu código antes de cada commit.

---

## Solução de Problemas

### Problemas Comuns e Soluções

#### Problema: "OPENAI_API_KEY not found"

**Solução:**

- Certifique-se de que o arquivo \`.env\` existe na raiz do projeto
- Verifique se a chave API está corretamente formatada
- Verifique se não há espaços extras ou aspas ao redor da chave

#### Problema: "ModuleNotFoundError"

**Solução:**

\`\`\`bash
# Certifique-se de que o ambiente virtual está ativado
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows

# Reinstale as dependências
pip install -r requirements.txt
\`\`\`

#### Problema: "Permission denied" ao instalar

**Solução:**

\`\`\`bash
# Não use sudo com ambientes virtuais
# Em vez disso, certifique-se de que o ambiente virtual está ativado primeiro
\`\`\`

#### Problema: Falha na conexão com Ollama

**Solução:**

\`\`\`bash
# Certifique-se de que o serviço Ollama está rodando
ollama serve

# Teste a conexão
ollama list
\`\`\`

---

## Próximos Passos

Agora que você tem tudo instalado:

1. Leia o [Guia de Início Rápido](uso-basico.md) para aprender o básico
2. Explore os [Exemplos](exemplos.md) para ver casos de uso do mundo real
3. Revise a [Arquitetura](../arquitetura.md) para entender o design do sistema
4. Confira a [Referência da API](../api.md) para documentação detalhada

---

## Requisitos do Sistema

### Requisitos Mínimos

- **SO**: Linux, macOS, Windows 10+
- **RAM**: 4GB (8GB recomendado)
- **Armazenamento**: 500MB para dependências
- **Python**: 3.10 ou superior

### Recomendado para Ollama

- **RAM**: 8GB+ (16GB para modelos maiores)
- **Armazenamento**: 10GB+ para modelos
- **CPU**: Processador multi-core

---

## Obtendo Ajuda

Se você encontrar algum problema:

- 📧 Email: estraliotojordan@gmail.com
- 🐛 Reportar bugs: [GitHub Issues](https://github.com/jor0105/AI_Agent/issues)
- 💬 Discussões: [GitHub Discussions](https://github.com/jor0105/AI_Agent/discussions)
