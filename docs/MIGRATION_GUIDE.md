## 📋 Checklist de Migração

### Para Todos os Usuários

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

## 📚 Recursos Adicionais

- [Documentação de Ferramentas](./tools.md)
- [Guia de Instalação](./guia/instalacao.md)
- [Exemplos de Uso](./guia/exemplos.md)
- [Exemplo de Lazy Loading](../examples/lazy_loading_demo.py)
