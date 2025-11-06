from pathlib import Path
from typing import Any, Dict, Optional

# import pandas as pd
# import PyPDF2
# import tiktoken
from src.domain import BaseTool


def _count_tokens(text: str) -> int:
    # enc = tiktoken.get_encoding("cl100k_base")
    # return len(enc.encode(text))
    test = 5
    return test


class ReadLocalFileTool(BaseTool):
    name = "read_local_file"
    description = "Lê arquivo local (txt,csv,excel,pdf,parquet). Retorna conteúdo como string ou erro se ultrapassar max_tokens."
    parameters: Dict[str, Any] = {
        "type": "object",
        "properties": {
            "path": {"type": "string"},
            "file_type": {
                "type": ["string", "null"],
                "enum": ["txt", "csv", "xls", "xlsx", "pdf", "parquet", None],
            },
            "max_tokens": {"type": "integer", "default": 30000},
        },
        "required": ["path"],
    }

    def execute(
        self,
        path: str,
        file_type: Optional[str] = None,
        max_tokens: int = 30000,
        **kwargs,
    ) -> str:
        p = Path(path)
        ext = (file_type or p.suffix.lstrip(".")).lower()
        if ext == "" or ext is None:
            ext = "txt"

        if ext in ("txt", "log", "md"):
            with open(p, "rb") as f:
                content = f.read().decode("utf-8", errors="replace")

        elif ext == "csv":
            df = pd.read_csv(p)
            content = df.to_csv(index=False)

        elif ext in ("xls", "xlsx"):
            df = pd.read_excel(p, sheet_name=0)
            content = df.to_csv(index=False)

        elif ext == "parquet":
            df = pd.read_parquet(p)
            content = df.to_csv(index=False)

        elif ext == "pdf":
            reader = PyPDF2.PdfReader(str(p))
            pages = [page.extract_text() or "" for page in reader.pages]
            content = "\n".join(pages)

        else:
            with open(p, "rb") as f:
                content = f.read().decode("utf-8", errors="replace")

        tokens = _count_tokens(content)
        if tokens > max_tokens:
            return f"ERROR: too_many_tokens ({tokens} > {max_tokens})"
        return content
