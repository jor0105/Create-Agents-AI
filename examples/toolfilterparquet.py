# Importe List e Union para a anotação de tipo correta
from typing import Any, Dict, List, Union

import pandas as pd

from src.domain import BaseTool  # Mantendo seu import


class DREQueryTool(BaseTool):
    """
    Uma ferramenta para consultar o arquivo Parquet da DRE consolidada
    de companhias abertas, filtrando por Código CVM.
    """

    name: str = "consultar_dre_por_cvm"
    description: str = (
        "Busca no arquivo Parquet 'dfp_cia_aberta_DRE_con_2024.parquet' "
        "os dados da DRE de uma empresa específica usando seu código CVM. "
        "Retorna as contas e valores (DS_CONTA, VL_CONTA)."
    )
    parameters: Dict[str, Any] = {
        "type": "object",
        "properties": {
            "cvm_code": {
                "type": "integer",
                "description": "O código CVM numérico da companhia a ser consultada.",
            }
        },
        "required": ["cvm_code"],
    }

    # O seu __init__ com o caminho absoluto está correto para seu uso
    def __init__(
        self,
        file_path: str = "/home/jordan/Downloads/Databases/dados_bolsa_br/Docs_Cvm/DFP/2024/dfp_cia_aberta_DRE_con_2024.parquet",
    ):
        """
        Inicializa a ferramenta com o caminho para o arquivo Parquet.

        Args:
            file_path (str): O caminho para o arquivo .parquet.
        """
        self.file_path = file_path

    # --- CORREÇÃO DA ASSINATURA E DOCSTRING ---
    def execute(self, cvm_code: int) -> Union[List[Dict[str, Any]], Dict[str, str]]:
        """
        Executa a consulta no arquivo Parquet.

        Args:
            cvm_code (int): O código CVM fornecido pelo agente.

        Returns:
            Uma lista de dicionários (contas e valores) em caso de sucesso,
            ou um dicionário de erro (Dict[str, str]) em caso de falha.
        """
        try:
            df = pd.read_parquet(self.file_path)
        except FileNotFoundError:
            # Retorno de erro (Dict[str, str])
            return {"error": f"Arquivo Parquet não encontrado em '{self.file_path}'."}
        except Exception as e:
            # Retorno de erro (Dict[str, str])
            return {"error": f"Erro ao ler o arquivo Parquet: {e}"}

        # Filtrar o DataFrame pelo CD_CVM
        filtered_df = df[df["CD_CVM"] == cvm_code]

        if filtered_df.empty:
            # Retorno de erro (Dict[str, str])
            return {"error": f"Nenhum dado encontrado para o código CVM {cvm_code}."}

        # Selecionar as colunas solicitadas
        result_df = filtered_df[["DS_CONTA", "VL_CONTA"]]

        # Retorno de sucesso (List[Dict[str, Any]])
        return result_df.to_dict(orient="records")


if __name__ == "__main__":
    # Exemplo de uso da ferramenta
    tool = DREQueryTool()

    # --- Teste de Sucesso ---
    # (Substitua 24910 por um código CVM que EXISTA no seu arquivo)
    cvm_code_sucesso = 1023
    print(f"\n--- Testando CVM Válido: {cvm_code_sucesso} ---")
    result_ok = tool.execute(cvm_code=cvm_code_sucesso)

    # O 'if' checa se o resultado é um dict e se tem a chave 'error'
    if isinstance(result_ok, dict) and "error" in result_ok:
        print(f"Erro: {result_ok['error']}")
    else:
        print(f"Sucesso: Encontrados {len(result_ok)} registros.")
        # print(result_ok) # Descomente para ver o JSON completo

    # --- Teste de Erro ---
    cvm_code_erro = 999999999
    print(f"\n--- Testando CVM Inválido: {cvm_code_erro} ---")
    result_err = tool.execute(cvm_code=cvm_code_erro)

    if isinstance(result_err, dict) and "error" in result_err:
        print(f"Sucesso (Erro esperado): {result_err['error']}")
    else:
        print("Falha no teste: Um erro era esperado, mas não ocorreu.")
