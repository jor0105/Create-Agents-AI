# 🔰 Guia de Logging

Sistema de logs automático do **AI Agent Creator**.

---

## 🤔 O que é Log?

**Log = Diário do seu sistema**

Registra automaticamente:

- ✅ Operações executadas
- ⚠️ Avisos importantes
- ❌ Erros encontrados

---

## ✅ É Automático!

Os logs já funcionam automaticamente:

```python
# Quando você cria um agente
agent = AIAgent(provider="openai", model="gpt-4")
# 📝 LOG: "Initializing AIAgent controller - Provider: openai, Model: gpt-4"

# Quando conversa
response = agent.chat("Olá!")
# 📝 LOG: "Chat request received - Message length: 4 chars"
# 📝 LOG: "Chat response generated - Response length: 50 chars"

# Quando dá erro
agent.chat("")  # Mensagem vazia
# 📝 LOG ERROR: "Mensagem vazia não permitida"
```

**Você NÃO precisa fazer NADA!**

---

## 👀 Onde Ver os Logs?

### No Terminal (Padrão)

Aparecem automaticamente enquanto roda:

```bash
$ python main.py

2025-11-08 10:30:45 - INFO - Initializing AIAgent controller
2025-11-08 10:30:46 - INFO - Chat request received
2025-11-08 10:30:48 - INFO - Chat response generated
```

### Em Arquivo (Opcional)

```python
from src.infra.config.logging_config import LoggingConfig

# Configure UMA VEZ no início
LoggingConfig.configure(log_to_file=True)

# Agora logs salvam em: logs/app.log
```

**Ver logs salvos:**

```bash
# Ver todo arquivo
cat logs/app.log

# Últimas 20 linhas
tail -20 logs/app.log

# Ver em tempo real
tail -f logs/app.log

# Ver só erros
grep ERROR logs/app.log
```

---

## 🔴 Quando Aparecem Erros?

**SEMPRE e AUTOMATICAMENTE!**

### No Terminal

```bash
$ python main.py

2025-11-08 10:30:45 - INFO - Tentando conectar...
2025-11-08 10:30:46 - ERROR - Falha na conexão
2025-11-08 10:30:46 - ERROR - Traceback completo...
```

### No Arquivo

```bash
$ cat logs/app.log

[2025-11-08 10:30:46] ERROR - Erro ao processar
[2025-11-08 10:30:46] ERROR - Exception: KeyError
```

---

## 📊 Níveis de Log

| Nível       | Quando          | O que mostra         |
| ----------- | --------------- | -------------------- |
| 🐛 DEBUG    | Desenvolvimento | Detalhes técnicos    |
| ℹ️ INFO     | Normal          | Operações principais |
| ⚠️ WARNING  | Alerta          | Algo estranho        |
| ❌ ERROR    | Erro            | Problema encontrado  |
| 🔥 CRITICAL | Grave           | Sistema quebrado     |

**Controlar nível:**

```python
import logging
from src.infra.config.logging_config import LoggingConfig

# Ver tudo
LoggingConfig.configure(level=logging.DEBUG)

# Normal (padrão)
LoggingConfig.configure(level=logging.INFO)

# Só erros
LoggingConfig.configure(level=logging.ERROR)
```

---

## 🛡️ Segurança Automática

Dados sensíveis são **automaticamente protegidos**:

```python
# Você acidentalmente tenta logar:
logger.info(f"User: usuario@email.com")
logger.info(f"Password: senha123")
logger.info(f"CPF: 123.456.789-00")

# O que é REALMENTE gravado:
# User: [EMAIL_REDACTED]
# Password: [PASSWORD_REDACTED]
# CPF: [CPF_REDACTED]
```

✅ **100% Automático!**

- Emails protegidos
- Senhas protegidas
- CPF/CNPJ protegidos
- Cartões de crédito protegidos
- API Keys protegidas

---

## 📁 Rotação Automática

Arquivos de log são automaticamente gerenciados:

```
logs/
├── app.log      ← Atual (até 10MB)
├── app.log.1    ← Ontem
├── app.log.2    ← Anteontem
├── app.log.3    ← 3 dias atrás
└── app.log.4    ← 4 dias atrás (mais antigo)

Total: ~50MB máximo
```

**É automático!** Você não precisa fazer nada.

---

## 🚀 Quick Start

### 1. Configure (uma vez)

```python
# main.py
from src.infra.config.logging_config import LoggingConfig

LoggingConfig.configure(log_to_file=True)
```

### 2. Use seu sistema normalmente

```python
from src.presentation import AIAgent

agent = AIAgent(provider="openai", model="gpt-4")
response = agent.chat("Olá!")
```

### 3. Ver logs

```bash
# No terminal (automático)
$ python main.py

# Depois, ver arquivo
$ cat logs/app.log
```

**PRONTO!** ✅

---

## ❓ FAQ

**P: Preciso adicionar logs no meu código?**
R: ❌ NÃO! Já está automático.

**P: Os logs aparecem sozinhos?**
R: ✅ SIM! No terminal automaticamente.

**P: Posso desativar?**
R: ✅ SIM! Configure `level=logging.CRITICAL`.

**P: Logs salvam dados sensíveis?**
R: ❌ NÃO! Automaticamente protegidos.

**P: Quanto espaço ocupam?**
R: Máximo de **50MB** (rotação automática).

---

## 💡 Resumo

### O que você precisa saber:

1. **Logs já funcionam** - Automático! ✅
2. **Você não precisa fazer nada** - Já configurado! ✅
3. **Aparecem no terminal** - Enquanto roda! ✅
4. **Protegem dados sensíveis** - Automático! ✅
5. **Rotação automática** - Não enche o disco! ✅

### Para começar:

```python
# main.py (primeira linha)
from src.infra.config.logging_config import LoggingConfig
LoggingConfig.configure(log_to_file=True)

# Resto do código... (sem mudanças)
```

**Simples assim!** 🚀

---

**Versão:** 1.0.0 | **Atualização:** Novembro 2025
