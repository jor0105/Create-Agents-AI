import pandas as pd


class ParquetFilterTool:
    def run(self, file_path: str, cnpj: str) -> pd.DataFrame:
        df = pd.read_parquet(file_path)
        filtrado = df[df["CNPJ_CIA"] == cnpj]
        return filtrado


if __name__ == "__main__":
    arquivo = "/home/jordan/Downloads/Databases/dados_bolsa_br/Docs_Cvm/DFP/2024/dfp_cia_aberta_DRE_con_2024.parquet"
    cnpj = "18.248.557/0001-46"
    tool = ParquetFilterTool()
    result = tool.run(arquivo, cnpj)
