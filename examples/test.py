import logging

from examples.websearchtool import WebSearchTool
from src import AIAgent
from src.infra.config.logging_config import LoggingConfig

LoggingConfig.configure(level=logging.ERROR)


# Inicializar as ferramentas
web_search_tool = WebSearchTool()

tools = ["readlocalfile", "currentdate"]

config = {
    # "temperature": 0.7,
    # "max_tokens": 300,
    "think": True,
}


agent = AIAgent(
    provider="ollama",
    model="deepseek-v3.1:671b-cloud",
    name="Agente AI",
    instructions="Você é um assistente inteligente que ajuda os usuários a responder perguntas e realizar tarefas.",
    config=config,
    tools=tools,
)


print("\n" + "=" * 100)
print("TESTE: Leitura Datas")
print("=" * 100)


arquivos = [
    "/home/jordan/Downloads/HistoricalQuotations_B3.pdf",
    "/home/jordan/Downloads/Petição inicial.pdf",
    "/home/jordan/Downloads/Carteira_EStudante.pdf",
    "/home/jordan/Downloads/Databases/Documentos_B3/Ações_do_IBOV.parquet",
    "/home/jordan/Downloads/Databases/Documentos_B3/Ações_B3.parquet",
    "/home/jordan/Downloads/cad_cia_aberta.csv",
    "/home/jordan/Downloads/Sem título 1.xlsx",
]

# caminho = "/home/jordan/Downloads/Petição inicial.pdf"

for caminho in arquivos:
    user_message = f"me diga algo sobre esse documento {caminho} e utilize max token acima de 100000 na tool"
    response = agent.chat(user_message)
    print("\n" + "-" * 100)
    print("\n" + "-" * 100)
    print(f"ARQUIVO: {caminho}")
    print(f"\nResposta do agente: {response}")
    print("\n" + "-" * 100)
