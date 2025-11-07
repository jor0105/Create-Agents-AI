#!/usr/bin/env python3
"""
Demonstração de Lazy Loading de Ferramentas

Este exemplo mostra como a biblioteca carrega ferramentas de forma inteligente,
importando dependências pesadas apenas quando necessário.
"""

import time


def demonstrate_import_speed():
    """Demonstra a diferença de velocidade com lazy loading."""
    print("=" * 70)
    print("🚀 DEMONSTRAÇÃO: Lazy Loading de Ferramentas")
    print("=" * 70)
    print()

    # 1. Importação básica (super rápida)
    print("1️⃣  Importando módulo básico...")
    start = time.time()

    elapsed = time.time() - start
    print(f"   ✅ Importado em {elapsed:.4f} segundos")
    print("   📦 Memória: ~50MB (sem pandas, tiktoken, pymupdf)")
    print()

    # 2. Importação de ferramenta leve (instantânea)
    print("2️⃣  Importando ferramenta leve (CurrentDateTool)...")
    start = time.time()
    from src.infra.adapters.Tools import CurrentDateTool

    elapsed = time.time() - start
    print(f"   ✅ Importado em {elapsed:.4f} segundos")

    tool = CurrentDateTool()
    result = tool.execute()
    print(f"   🕒 Data atual: {result}")
    print()

    # 3. Verificar ferramentas disponíveis
    print("3️⃣  Verificando ferramentas disponíveis...")
    from src.infra.config.available_tools import AvailableTools

    tools = AvailableTools.get_available_tools()
    print(f"   📋 Total de ferramentas: {len(tools)}")

    for name, tool in tools.items():
        status = "✅" if tool else "⚠️"
        print(f"   {status} {name}: {tool.name if tool else 'não disponível'}")
    print()

    # 4. Tentar usar ferramenta pesada (ReadLocalFileTool)
    print("4️⃣  Tentando usar ReadLocalFileTool (ferramenta pesada)...")
    try:
        start = time.time()
        from src.infra.adapters.Tools import ReadLocalFileTool

        elapsed = time.time() - start

        print(f"   ✅ ReadLocalFileTool importada em {elapsed:.4f} segundos")
        print("   📦 Memória adicional: ~150MB (pandas, tiktoken, pymupdf)")

        # Criar instância
        read_tool = ReadLocalFileTool()
        print("   ✅ Ferramenta inicializada com sucesso!")
        print(f"   📝 Descrição: {read_tool.description.strip()[:80]}...")

    except ImportError:
        print("   ⚠️  ReadLocalFileTool não disponível")
        print("   💡 Razão: Dependências opcionais não instaladas")
        print()
        print("   📦 Para instalar:")
        print("      pip install ai-agent[file-tools]")
        print("      # ou")
        print("      poetry install -E file-tools")
        print()
        print(
            "   ℹ️  Isso instalará: tiktoken, pymupdf, pandas, openpyxl, pyarrow, chardet"
        )

    print()
    print("=" * 70)


def demonstrate_tool_usage():
    """Demonstra o uso prático das ferramentas."""
    print()
    print("=" * 70)
    print("🛠️  DEMONSTRAÇÃO: Uso de Ferramentas")
    print("=" * 70)
    print()

    # Usar ferramenta de data
    print("1️⃣  Usando CurrentDateTool...")
    from src.infra.adapters.Tools import CurrentDateTool

    date_tool = CurrentDateTool()
    current_date = date_tool.execute()
    print(f"   📅 Data/Hora atual: {current_date}")
    print()

    # Tentar usar ferramenta de leitura
    print("2️⃣  Verificando disponibilidade de ReadLocalFileTool...")
    from src.infra.config.available_tools import AvailableTools

    tools = AvailableTools.get_available_tools()

    if "readlocalfile" in tools and tools["readlocalfile"]:
        print("   ✅ ReadLocalFileTool disponível!")
        print()
        print("   📖 Exemplo de uso:")
        print("   ```python")
        print("   from src.infra.adapters.Tools import ReadLocalFileTool")
        print()
        print("   tool = ReadLocalFileTool()")
        print("   content = tool.execute(")
        print("       path='/caminho/para/arquivo.pdf',")
        print("       max_tokens=30000")
        print("   )")
        print("   print(content)")
        print("   ```")
    else:
        print("   ⚠️  ReadLocalFileTool não disponível")
        print("   💡 Instale com: poetry install -E file-tools")

    print()
    print("=" * 70)


def demonstrate_agent_with_tools():
    """Demonstra criação de agente com ferramentas."""
    print()
    print("=" * 70)
    print("🤖 DEMONSTRAÇÃO: Agente com Ferramentas")
    print("=" * 70)
    print()

    try:
        from src.presentation import AIAgent

        print("1️⃣  Criando agente com ferramentas disponíveis...")
        print()

        # Verificar quais ferramentas estão disponíveis
        from src.infra.config.available_tools import AvailableTools

        tools = AvailableTools.get_available_tools()

        print(f"   📋 Ferramentas disponíveis para o agente: {len(tools)}")
        for name in tools:
            print(f"      • {name}")

        print()
        print("   💡 O agente pode usar essas ferramentas automaticamente!")
        print()
        print("   Exemplo:")
        print("   ```python")
        print("   agent = AIAgent(")
        print("       model='gpt-4',")
        print("       name='Assistente',")
        print("       instructions='Você pode usar ferramentas quando necessário'")
        print("   )")
        print()
        print("   # O agente usará CurrentDateTool automaticamente")
        print("   response = agent.chat('Que dia é hoje?')")
        print()
        if "readlocalfile" in tools:
            print("   # O agente usará ReadLocalFileTool automaticamente")
            print("   response = agent.chat('Resuma o arquivo documento.pdf')")
        print("   ```")

    except ImportError as e:
        print(f"   ⚠️  Não foi possível importar AIAgent: {e}")

    print()
    print("=" * 70)


def main():
    """Executa todas as demonstrações."""
    print()
    print("╔" + "═" * 68 + "╗")
    print("║" + " " * 15 + "LAZY LOADING DEMONSTRATION" + " " * 27 + "║")
    print("║" + " " * 20 + "AI Agent Creator" + " " * 32 + "║")
    print("╚" + "═" * 68 + "╝")
    print()

    try:
        demonstrate_import_speed()
        demonstrate_tool_usage()
        demonstrate_agent_with_tools()

        print()
        print("✅ Demonstração concluída!")
        print()
        print("📚 Para mais informações:")
        print("   • README.md - Guia de instalação")
        print("   • docs/tools.md - Documentação completa de ferramentas")
        print("   • docs/guia/exemplos.md - Mais exemplos de uso")
        print()

    except Exception as e:
        print(f"❌ Erro durante demonstração: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
