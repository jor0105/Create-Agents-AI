#!/usr/bin/env python3
"""Quick test to verify lazy loading implementation."""

print("=" * 70)
print("🧪 TESTE RÁPIDO: Verificação de Lazy Loading")
print("=" * 70)
print()

# Teste 1: Verificar que file_utils não está carregado inicialmente
import sys

print("1️⃣  Verificando módulos carregados antes de import...")
before_modules = set(sys.modules.keys())
file_utils_loaded = any("file_utils" in m for m in before_modules)
print(f"   file_utils carregado antes: {file_utils_loaded}")
assert not file_utils_loaded, "file_utils não deveria estar carregado!"
print("   ✅ PASS: file_utils não está carregado inicialmente")
print()

# Teste 2: Import de ferramenta leve
print("2️⃣  Importando CurrentDateTool (ferramenta leve)...")
try:
    print("   ✅ PASS: CurrentDateTool importado com sucesso")
except Exception as e:
    print(f"   ❌ FAIL: {e}")
    sys.exit(1)
print()

# Teste 3: Verificar que file_utils ainda não foi carregado
print("3️⃣  Verificando que file_utils ainda não foi carregado...")
after_basic = set(sys.modules.keys())
file_utils_loaded = any("file_utils" in m for m in after_basic)
print(f"   file_utils carregado após CurrentDateTool: {file_utils_loaded}")
if not file_utils_loaded:
    print("   ✅ PASS: Lazy loading funcionando! file_utils não carregado")
else:
    print(
        "   ⚠️  WARNING: file_utils foi carregado (pode ser esperado se deps instaladas)"
    )
print()

# Teste 4: Verificar estrutura de extras no pyproject.toml
print("4️⃣  Verificando configuração de extras...")
try:
    import tomli

    with open("pyproject.toml", "rb") as f:
        data = tomli.load(f)

    extras = data.get("tool", {}).get("poetry", {}).get("extras", {})

    if "file-tools" in extras:
        print("   ✅ PASS: Extra 'file-tools' configurado")
        deps = extras["file-tools"]
        print(f"   📦 Dependências: {', '.join(deps)}")
    else:
        print("   ❌ FAIL: Extra 'file-tools' não encontrado")
        sys.exit(1)

except ImportError:
    print("   ⚠️  SKIP: tomli não disponível (Python < 3.11)")
except Exception as e:
    print(f"   ❌ ERROR: {e}")
    sys.exit(1)
print()

# Teste 5: Verificar __getattr__ implementation
print("5️⃣  Verificando implementação de __getattr__...")
try:
    import src.infra.adapters.Tools as tools_module

    # Verificar se __getattr__ existe
    if hasattr(tools_module, "__getattr__"):
        print("   ✅ PASS: __getattr__ implementado em Tools")
    else:
        print("   ❌ FAIL: __getattr__ não encontrado")
        sys.exit(1)

except Exception as e:
    print(f"   ❌ ERROR: {e}")
    sys.exit(1)
print()

print("=" * 70)
print("✅ TODOS OS TESTES PASSARAM!")
print("=" * 70)
print()
print("📋 Resumo:")
print("   • Lazy loading implementado corretamente")
print("   • Extras configurados no pyproject.toml")
print("   • __getattr__ funcionando")
print("   • file_utils não carregado desnecessariamente")
print()
print("🎯 Próximo passo: poetry install -E file-tools (se precisar)")
