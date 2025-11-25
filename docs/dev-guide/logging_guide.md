# 📝 Guia de Logging

Este guia explica como configurar e utilizar o sistema de logging da biblioteca `CreateAgentsAI`. Seguindo as melhores práticas para bibliotecas Python, o logging é **silencioso por padrão** para não poluir a saída da sua aplicação.

______________________________________________________________________

## 🔇 Comportamento Padrão

Ao importar e usar a biblioteca, nenhum log será exibido no console ou salvo em arquivo, a menos que você configure explicitamente o sistema de logging.

Isso é feito intencionalmente para evitar conflitos com a configuração de logging da aplicação que consome a biblioteca.

______________________________________________________________________

## 🛠️ Como Ativar Logs

### Opção 1: Configuração Rápida (Desenvolvimento)

Para desenvolvimento, testes ou scripts simples, use o helper `configure_for_development`:

```python
import logging
from createagents import LoggingConfig

# Ativa logs no nível INFO
LoggingConfig.configure_for_development(level=logging.INFO)

# Ou para ver tudo (DEBUG)
LoggingConfig.configure_for_development(level=logging.DEBUG)
```

Isso configurará logs coloridos no console e filtragem automática de dados sensíveis.

### Opção 2: Configuração Padrão do Python

Se sua aplicação já configura o logging, a biblioteca respeitará essa configuração:

```python
import logging

# Configuração da sua aplicação
logging.basicConfig(level=logging.INFO)

# Agora os logs da biblioteca aparecerão
from createagents import CreateAgent
```

### Opção 3: Configuração Avançada

Para controlar apenas os logs da biblioteca:

```python
import logging

# Configura apenas o logger 'createagents'
logger = logging.getLogger("createagents")
logger.setLevel(logging.DEBUG)
logger.addHandler(logging.StreamHandler())
```

______________________________________________________________________

## 🔒 Segurança e Privacidade

A biblioteca inclui recursos automáticos de segurança nos logs:

- **Sanitização**: Chaves de API, senhas e tokens são mascarados automaticamente (ex: `[API_KEY_REDACTED]`).
- **Filtros**: Em produção, você pode configurar para logar apenas erros.

______________________________________________________________________

## ⚙️ Variáveis de Ambiente

Você pode controlar o logging através de variáveis de ambiente (se usar `LoggingConfig.configure()`):

| Variável          | Descrição                                  | Padrão       |
| ----------------- | ------------------------------------------ | ------------ |
| `LOG_LEVEL`       | Nível de log (DEBUG, INFO, WARNING, ERROR) | INFO         |
| `LOG_TO_FILE`     | Salvar logs em arquivo (true/false)        | false        |
| `LOG_FILE_PATH`   | Caminho do arquivo de log                  | logs/app.log |
| `LOG_JSON_FORMAT` | Usar formato JSON estruturado              | false        |

______________________________________________________________________

## 📊 Logs em JSON (Produção)

Para ambientes de produção com agregação de logs (Datadog, CloudWatch, ELK), ative o formato JSON:

```python
LoggingConfig.configure(json_format=True)
```

Ou via ambiente:

```bash
export LOG_JSON_FORMAT=true
```

Isso gerará logs estruturados fáceis de indexar:

```json
{
  "timestamp": "2024-03-20 10:00:00,000",
  "level": "INFO",
  "logger": "createagents.service",
  "message": "Agent initialized",
  "module": "service",
  "line": 42
}
```
