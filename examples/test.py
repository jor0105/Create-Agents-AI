import logging

from examples.websearchtool import WebSearchTool
from src import AIAgent
from src.infra.config.logging_config import LoggingConfig

LoggingConfig.configure(level=logging.ERROR)


# Inicializar as ferramentas
web_search_tool = WebSearchTool()

tools = ["readlocalfile"]

# config = {
#     "temperature": 0.7,
#     "max_tokens": 300,
# }

# agent = AIAgent(
#     provider="openai",
#     model="gpt-5-mini",
#     name="AgenteTeste",
#     instructions="Responda como um assistente educado.",
#     # config=config,
#     tools=tools,
# )
# user_message = "Olá, quem é você?"
# response = agent.chat(user_message)
# print(f"Resposta do agente: {response}")
# print(f"Agente criado: {agent}")


# Segundo exemplo de uso do AIAgent
agent2 = AIAgent(
    provider="ollama",
    model="gpt-oss:120b-cloud",
    name="Agente Ollama",
    instructions="Você é um assistente que pode buscar informações lendo arquivos locais. Sempre que precisar de informações atualizadas, use a ferramenta de busca web. Quando precisar ler um arquivo, use a ferramenta de leitura de arquivos.",
    # config=config,
    tools=tools,
)

# Teste 1: Busca na web
# print("=" * 100)
# print("TESTE 1: Busca na Web")
# print("=" * 100)


# Teste 2: Leitura de arquivo (primeiro vamos criar um arquivo de teste)
print("\n" + "=" * 100)
print("TESTE 2: Leitura de Arquivo")
print("=" * 100)


arquivos = [
    "/home/jordan/Downloads/MAPA.docx",
    "/home/jordan/Downloads/HistoricalQuotations_B3.pdf",
    "/home/jordan/Downloads/ibovespa.png",
    "/home/jordan/Downloads/Petição inicial.pdf",
    "/home/jordan/Downloads/Carteira_EStudante.pdf",
    "/home/jordan/Downloads/Databases/Documentos_B3/Ações_B3.parquet",
    "/home/jordan/Downloads/Databases/Documentos_B3/Ações_do_IBOV.parquet",
    "/home/jordan/Downloads/cad_cia_aberta.csv",
]

caminho = "/home/jordan/Downloads/cad_cia_aberta.csv"

# for caminho in arquivos:
user_message = f"Leia o arquivo {caminho} e me dê um resumo do conteúdo dele. Use a tool 'readlocalfile' para ler o arquivo e coloque max_tokens=100000."
response = agent2.chat(user_message)
print("\n" + "-" * 100)
print(f"ARQUIVO: {caminho}")
print(f"\nResposta do agente: {response}")
print("\n" + "-" * 100)
