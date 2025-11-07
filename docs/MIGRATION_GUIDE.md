# 📦 Guia de Migração: Lazy Loading e Dependências Opcionais

## 🎯 Objetivo

Este guia ajuda você a migrar do sistema antigo (onde todas as dependências eram obrigatórias) para o novo sistema com **lazy loading** e **dependências opcionais**.

## ⚡ O Que Mudou?

### Antes (Versão < 0.2.0)

```python
# Todas as dependências eram instaladas automaticamente
poetry install  # Instalava: pandas, tiktoken, pymupdf, openpyxl, pyarrow, chardet

# Importação carregava TUDO de uma vez (~2-3 segundos)
from src.infra.adapters import ReadLocalFileTool  # Carrega pandas, tiktoken, etc
```

**Problemas:**
- ❌ Instalação lenta (~100MB+ de dependências)
- ❌ Import lento (~2-3 segundos)
- ❌ Alto uso de memória (~200MB) mesmo sem usar ferramentas pesadas
- ❌ Usuários sem necessidade de ler arquivos pagavam o custo

### Agora (Versão >= 0.2.0)

```python
# Instalação modular
poetry install              # Básico (~20MB)
poetry install -E file-tools  # + Ferramentas de arquivo (~100MB)

# Importação inteligente (lazy loading)
from src.infra.adapters import CurrentDateTool  # Instantâneo
from src.infra.adapters import ReadLocalFileTool  # Carrega só quando usado
```

**Benefícios:**
- ✅ Instalação rápida (só o que você precisa)
- ✅ Import rápido (~0.1 segundos para básico)
- ✅ Memória otimizada (só carrega quando usa)
- ✅ Flexibilidade total

## 🚀 Guia de Migração Passo a Passo

### Passo 1: Atualizar Dependências

**Se você NÃO usa ferramentas de leitura de arquivos:**

```bash
# Remover lock file antigo
rm poetry.lock

# Instalar só o básico
poetry install
```

**Se você USA ferramentas de leitura de arquivos (ReadLocalFileTool):**

```bash
# Remover lock file antigo
rm poetry.lock

# Instalar com extras
poetry install -E file-tools
```

### Passo 2: Verificar Importações

**Antes (código antigo):**
```python
# Funcionava, mas sempre carregava tudo
from src.infra.adapters import ReadLocalFileTool, CurrentDateTool
```

**Agora (recomendado):**
```python
# Opção 1: Import direto (lazy loading automático)
from src.infra.adapters import CurrentDateTool
from src.infra.adapters import ReadLocalFileTool  # Só carrega quando executado

# Opção 2: Import seletivo
from src.infra.adapters.Tools import CurrentDateTool
from src.infra.adapters.Tools import ReadLocalFileTool  # Com validação
```

### Passo 3: Adicionar Tratamento de Erros (Opcional mas Recomendado)

**Para código robusto:**

```python
from src.infra.config.available_tools import AvailableTools

# Verificar ferramentas disponíveis
tools = AvailableTools.get_available_tools()

if "readlocalfile" in tools and tools["readlocalfile"]:
    # ReadLocalFileTool está disponível
    from src.infra.adapters.Tools import ReadLocalFileTool
    tool = ReadLocalFileTool()
    result = tool.execute(path="file.pdf")
else:
    # Ferramenta não disponível
    print("⚠️ ReadLocalFileTool não instalada")
    print("💡 Instale com: poetry install -E file-tools")
```

**Ou com try/except:**

```python
try:
    from src.infra.adapters.Tools import ReadLocalFileTool
    tool = ReadLocalFileTool()
    result = tool.execute(path="file.pdf")
except ImportError:
    print("⚠️ ReadLocalFileTool requer: poetry install -E file-tools")
    # Fallback ou tratamento alternativo
```

### Passo 4: Atualizar Testes

**Se seus testes usam ReadLocalFileTool:**

```python
# conftest.py ou no topo do arquivo de teste
pytest.importorskip(
    "src.infra.adapters.Tools.ReadLocalFileTool",
    reason="Requer file-tools extras: poetry install -E file-tools"
)
```

**Ou com skip condicional:**

```python
import pytest

# Tentar importar
try:
    from src.infra.adapters.Tools import ReadLocalFileTool
    HAS_FILE_TOOLS = True
except ImportError:
    HAS_FILE_TOOLS = False

# Pular teste se não disponível
@pytest.mark.skipif(not HAS_FILE_TOOLS, reason="file-tools not installed")
def test_read_local_file():
    tool = ReadLocalFileTool()
    # ... resto do teste
```

## 📋 Checklist de Migração

### Para Todos os Usuários

- [ ] Atualizar código para versão >= 0.2.0
- [ ] Remover `poetry.lock` antigo
- [ ] Executar `poetry install` (ou com extras necessários)
- [ ] Verificar que imports básicos funcionam
- [ ] Executar testes

### Se Você Usa ReadLocalFileTool

- [ ] Executar `poetry install -E file-tools`
- [ ] Verificar que ReadLocalFileTool importa corretamente
- [ ] Adicionar tratamento de erros (opcional)
- [ ] Atualizar testes com skip condicional (opcional)

### Para Ambientes de Produção

- [ ] Atualizar `requirements.txt` ou `pyproject.toml` no CI/CD
- [ ] Adicionar extras necessários: `pip install ai-agent[file-tools]`
- [ ] Testar deploy em ambiente de staging
- [ ] Verificar logs para warnings de ferramentas ausentes
- [ ] Deploy em produção

## 🔍 Verificação Pós-Migração

Execute o script de demonstração para verificar:

```bash
python examples/lazy_loading_demo.py
```

Você deve ver:
- ✅ Importações rápidas
- ✅ Ferramentas disponíveis listadas
- ✅ Nenhum erro de import (ou erros claros se extras faltam)

## 🆘 Resolução de Problemas

### Problema: `ImportError: ReadLocalFileTool requires optional dependencies`

**Solução:**
```bash
poetry install -E file-tools
# ou
pip install ai-agent[file-tools]
```

### Problema: `ModuleNotFoundError: No module named 'pandas'`

**Causa:** Você está tentando usar ReadLocalFileTool sem instalar os extras.

**Solução:**
```bash
poetry install -E file-tools
```

### Problema: Importações estão lentas

**Diagnóstico:**
```python
import time

start = time.time()
from src.infra import adapters
print(f"Import levou {time.time() - start:.2f}s")
```

**Se > 1 segundo:**
- Verifique se está importando ReadLocalFileTool desnecessariamente
- Use lazy imports ou verificação condicional

### Problema: Testes falhando após migração

**Se teste usa ReadLocalFileTool:**

```python
# Adicione no início do teste
pytest.importorskip("pandas", reason="file-tools required")
```

**Ou no conftest.py:**
```python
import pytest

def pytest_configure(config):
    config.addinivalue_line(
        "markers", "file_tools: tests that require file-tools extras"
    )

@pytest.fixture
def skip_if_no_file_tools():
    try:
        import pandas
        import tiktoken
    except ImportError:
        pytest.skip("file-tools extras not installed")
```

## 📊 Comparação de Performance

### Tempo de Instalação

| Método | Tempo | Tamanho |
|--------|-------|---------|
| Básico (novo) | ~30s | ~20MB |
| Com file-tools | ~90s | ~120MB |
| Tudo (antigo) | ~90s | ~120MB |

### Tempo de Import

| Import | Antigo | Novo |
|--------|--------|------|
| Módulo básico | ~2.5s | ~0.1s |
| CurrentDateTool | ~2.5s | ~0.1s |
| ReadLocalFileTool | ~2.5s | ~2.0s (só quando usado) |

### Uso de Memória

| Cenário | Antigo | Novo |
|---------|--------|------|
| Só agente básico | ~200MB | ~50MB |
| Com CurrentDateTool | ~200MB | ~50MB |
| Com ReadLocalFileTool | ~200MB | ~200MB |

## 🎉 Benefícios da Migração

1. **Instalação mais rápida** - Só instala o que você precisa
2. **Imports mais rápidos** - Carrega sob demanda
3. **Menor uso de memória** - Não carrega dependências desnecessárias
4. **Código mais limpo** - Erro claro quando faltam dependências
5. **Melhor experiência** - Instalação granular por caso de uso

## 📚 Recursos Adicionais

- [Documentação de Ferramentas](./tools.md)
- [Guia de Instalação](./guia/instalacao.md)
- [Exemplos de Uso](./guia/exemplos.md)
- [Exemplo de Lazy Loading](../examples/lazy_loading_demo.py)

## 🤝 Suporte

Precisa de ajuda com a migração?

- 📖 [FAQ](./tools.md#-faq)
- 🐛 [Reportar Problemas](https://github.com/jor0105/AI_Agent/issues)
- 💬 [Discussões](https://github.com/jor0105/AI_Agent/discussions)

---

**Última atualização:** Novembro 2025
