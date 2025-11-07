import logging

from examples.websearchtool import WebSearchTool
from src import AIAgent
from src.infra.config.logging_config import LoggingConfig

LoggingConfig.configure(level=logging.ERROR)


# Inicializar as ferramentas
web_search_tool = WebSearchTool()

tools = ["readlocalfile"]

config = {
    "temperature": 1,
    # "max_tokens": 300,
}


agent = AIAgent(
    provider="openai",
    model="gpt-4.1-mini",
    name="Agente AI",
    instructions="Você é um assistente que pode buscar informações lendo arquivos locais. Sempre que precisar de informações atualizadas, use a ferramenta de busca web. Quando precisar ler um arquivo, use a ferramenta de leitura de arquivos.",
    config=config,
    tools=tools,
)


print("\n" + "=" * 100)
print("TESTE: Leitura de Arquivo")
print("=" * 100)


arquivos = [
    "/home/jordan/Downloads/HistoricalQuotations_B3.pdf",
    "/home/jordan/Downloads/ibovespa.png",
    "/home/jordan/Downloads/Petição inicial.pdf",
    "/home/jordan/Downloads/Carteira_EStudante.pdf",
    "/home/jordan/Downloads/Databases/Documentos_B3/Ações_B3.parquet",
    "/home/jordan/Downloads/Databases/Documentos_B3/Ações_do_IBOV.parquet",
    "/home/jordan/Downloads/cad_cia_aberta.csv",
    "/home/jordan/Downloads/Sem título 1.xlsx",
]

caminho = "/home/jordan/Downloads/HistoricalQuotations_B3.pdf"
user_message = f"me diga algo sobre esse documento {caminho}"
response = agent.chat(user_message)
metrics = agent.get_metrics()
print("\n" + "-" * 100)
print(f"\nResposta do agente: {response}")
print("\n" + "-" * 100)
print(f"Métricas: {metrics}")


# for caminho in arquivos:

# user_message = f"Leia o arquivo {caminho} e me dê um resumo do conteúdo dele. Use a tool 'readlocalfile' para ler o arquivo e coloque max_tokens=100000."
# response = agent.chat(user_message)
# print("\n" + "-" * 100)
# print(f"ARQUIVO: {caminho}")
# print(f"\nResposta do agente: {response}")
# print("\n" + "-" * 100)
