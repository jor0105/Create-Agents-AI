# Como Contribuir

Contribua para o desenvolvimento do **Create Agents AI** seguindo as diretrizes abaixo. Toda colaboração é bem-vinda!

______________________________________________________________________

## 🚦 Requisitos para Contribuição

- Python 3.12+ e Poetry instalados
- Conhecimento básico de Clean Architecture e SOLID
- Familiaridade com Git e GitHub
- Seguir o padrão de código, testes e documentação do projeto

______________________________________________________________________

## 🛠️ Passo a Passo para Contribuir

1. **Fork** o repositório no GitHub
1. **Clone** seu fork localmente:
   ```bash
   git clone https://github.com/seu-usuario/Create-Agents-AI.git
   cd Create-Agents-AI
   ```
1. **Crie uma branch** descritiva:
   ```bash
   git checkout -b feature/nome-da-sua-feature
   ```
1. **Implemente** sua melhoria ou correção seguindo os padrões do projeto
1. **Adicione ou atualize testes** (unitários, integração, etc.)
1. **Garanta que todos os checks passem:**
   ```bash
   poetry run pre-commit run --all-files
   poetry run pytest --cov=src
   ```
1. **Atualize a documentação** se necessário (ex: novos parâmetros, exemplos, etc.)
1. **Faça commit seguindo o padrão Conventional Commits** (ex: `feat:`, `fix:`, `docs:`)
1. **Envie seu Pull Request (PR)** para o branch `develop` com uma descrição clara
1. Aguarde revisão e responda a eventuais comentários dos mantenedores

______________________________________________________________________

## ✅ Checklist de Qualidade para PR

- [ ] Código segue Clean Architecture e SOLID
- [ ] Testes automatizados cobrindo a nova funcionalidade/correção
- [ ] Documentação atualizada (código e Markdown)
- [ ] Sem warnings/lints (Black, Ruff, isort, yamllint, mdformat)
- [ ] Commits claros e atômicos
- [ ] PR descreve claramente o que foi feito e por quê

______________________________________________________________________

## 📝 Padrão de Commits

Utilize o padrão [Conventional Commits](https://www.conventionalcommits.org/pt-br/v1.0.0/):

- `feat:` Nova funcionalidade
- `fix:` Correção de bug
- `docs:` Mudança apenas na documentação
- `test:` Adição/melhoria de testes
- `refactor:` Refatoração sem alterar comportamento
- `chore:` Tarefas de manutenção

Exemplo:

```bash
git commit -m "feat: adicionar suporte ao provedor XYZ"
```

______________________________________________________________________

## 📚 Exemplos de Contribuição

- Adicionar nova ferramenta (Tool) customizada
- Corrigir bug em adapter de provedor
- Melhorar cobertura de testes
- Atualizar exemplos na documentação
- Sugerir melhorias de performance ou segurança

______________________________________________________________________

## 🐞 Reportar Bugs e Sugerir Melhorias

1. [Abra uma issue](https://github.com/jor0105/Create-Agents-AI/issues)
1. Descreva o problema/sugestão com detalhes, passos para reproduzir e contexto
1. Inclua logs, prints ou exemplos de código se possível

______________________________________________________________________

## 📖 Dicas para Documentação

- Sempre documente novas funções, classes e parâmetros com docstrings
- Atualize os arquivos Markdown relevantes em `docs/` (ex: exemplos, API, FAQ)
- Use português claro, técnico e acessível
- Inclua exemplos de uso sempre que possível

______________________________________________________________________

## 🤝 Contato e Suporte

- Email: estraliotojordan@gmail.com
- GitHub: [@jor0105](https://github.com/jor0105)
- Discussões: [GitHub Discussions](https://github.com/jor0105/Create-Agents-AI/discussions)

______________________________________________________________________

**Obrigado por contribuir! Seu apoio torna o projeto melhor para toda a comunidade.**
