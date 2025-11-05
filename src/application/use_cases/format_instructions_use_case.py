from typing import List, Optional

from src.domain import BaseTool


class FormatInstructionsUseCase:
    def execute(
        self, instructions: Optional[str] = None, tools: Optional[List[BaseTool]] = None
    ) -> Optional[str]:
        if not tools and not instructions:
            return None

        if tools:
            prompt_part = "Você pode usar as seguintes ferramentas:\n\n"
            for tool in tools:
                schema = tool.get_schema_for_llm()
                prompt_part += "<tool>\n"
                prompt_part += f"  <name>{schema['name']}</name>\n"
                prompt_part += f"  <description>{schema['description']}</description>\n"
                prompt_part += "</tool>\n\n"

        if not instructions:
            instructions = prompt_part
            return instructions

        return instructions + "\n\n" + prompt_part
