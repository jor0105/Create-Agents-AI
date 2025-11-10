import logging
from typing import Sequence, Union

from examples.toolfilterparquet import DREQueryTool
from examples.websearchtool import WebSearchTool
from src import AIAgent
from src.domain import BaseTool
from src.infra.config.logging_config import LoggingConfig

LoggingConfig.configure(level=logging.ERROR)


# Inicializar as ferramentas
tools: Sequence[Union[str, BaseTool]] = [
    WebSearchTool(),
    DREQueryTool(),
    "readlocalfile",
    "currentdate",
]

config = {
    "temperature": 0.5,
    # "max_tokens": 300,
    "think": True,
}


agent = AIAgent(
    provider="ollama",
    model="granite4:latest",
    name="Agente AI",
    instructions="Você é um assistente inteligente que ajuda os usuários a responder perguntas e realizar tarefas.",
    config=config,
    tools=tools,
)


print("\n" + "=" * 100)
print("TESTE: Leitura Datas")
print("=" * 100)


arquivos = [
    # "/home/jordan/Downloads/HistoricalQuotations_B3.pdf",
    "/home/jordan/Downloads/Petição inicial.pdf",
    "/home/jordan/Downloads/Carteira_EStudante.pdf",
    "/home/jordan/Downloads/Databases/Documentos_B3/Ações_do_IBOV.parquet",
    # "/home/jordan/Downloads/Databases/Documentos_B3/Ações_B3.parquet",
    "/home/jordan/Downloads/cad_cia_aberta.csv",
    "/home/jordan/Downloads/Sem título 1.xlsx",
    "/home/jordan/Downloads/MAPA.docx",
    "/home/jordan/Downloads/simple_exam_1.pdf",
    "/home/jordan/Downloads/Agravo de Petição - versão 5.docx",
]

caminho = "/home/jordan/Downloads/Databases/dados_bolsa_br/Docs_Cvm/DFP/2024/dfp_cia_aberta_DRE_con_2024.parquet"

# for caminho in arquivos:

user_message = "pesquise qual é o código cvm da empresa banco do brasil s.a na internet e depois utilize ele para pegar os dados dessa empresa pela tool DREQueryTool. Ao finalizar, faça uma análise completa sobre o DRE da empresa."
response = agent.chat(user_message)
print("\n" + "-" * 100)
print("\n" + "-" * 100)
print(f"ARQUIVO: {caminho}")
print(f"\nResposta do agente: {response}")
print("\n" + "-" * 100)
