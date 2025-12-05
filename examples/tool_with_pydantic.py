"""
Exemplo de uso do @tool com Pydantic para validação avançada.

Este arquivo demonstra:
1. Criação de args_schema com Pydantic BaseModel
2. Validação customizada com field_validator
3. Campos com restrições (ge, le, regex, etc.)
4. Tipos complexos (List, Optional, Literal)
5. Documentação automática via Field
"""

import asyncio
import logging
from typing import List, Literal, Optional

from pydantic import BaseModel, Field, field_validator

from createagents import CreateAgent, tool, LoggingConfigurator

# Habilitar logging para ver os passos da IA
LoggingConfigurator.configure(level=logging.INFO)


# =============================================================================
# Exemplo 1: Schema Básico com Field
# =============================================================================


class TemperatureInput(BaseModel):
    """Schema para conversão de temperatura."""

    value: float = Field(description='Valor da temperatura')
    from_unit: Literal['celsius', 'fahrenheit', 'kelvin'] = Field(
        default='celsius', description='Unidade de origem'
    )
    to_unit: Literal['celsius', 'fahrenheit', 'kelvin'] = Field(
        default='fahrenheit', description='Unidade de destino'
    )


@tool(args_schema=TemperatureInput)
def convert_temperature(
    value: float, from_unit: str = 'celsius', to_unit: str = 'fahrenheit'
) -> str:
    """Converter temperatura entre unidades.

    Args:
        value: Valor da temperatura.
        from_unit: Unidade de origem (celsius, fahrenheit, kelvin).
        to_unit: Unidade de destino (celsius, fahrenheit, kelvin).

    Returns:
        Temperatura convertida com explicação.
    """
    # Converter para Celsius primeiro
    if from_unit == 'celsius':
        celsius = value
    elif from_unit == 'fahrenheit':
        celsius = (value - 32) * 5 / 9
    else:  # kelvin
        celsius = value - 273.15

    # Converter de Celsius para unidade destino
    if to_unit == 'celsius':
        result = celsius
    elif to_unit == 'fahrenheit':
        result = celsius * 9 / 5 + 32
    else:  # kelvin
        result = celsius + 273.15

    return f'{value}° {from_unit} = {result:.2f}° {to_unit}'


# =============================================================================
# Exemplo 2: Validação Customizada
# =============================================================================


class ProductSearchInput(BaseModel):
    """Schema para busca de produtos com validação."""

    query: str = Field(
        min_length=2, max_length=100, description='Termo de busca'
    )
    category: Optional[str] = Field(
        default=None, description='Categoria do produto'
    )
    min_price: float = Field(
        default=0, ge=0, description='Preço mínimo (>= 0)'
    )
    max_price: float = Field(
        default=10000, le=100000, description='Preço máximo (<= 100000)'
    )
    sort_by: Literal['relevance', 'price_asc', 'price_desc', 'rating'] = Field(
        default='relevance', description='Ordenação dos resultados'
    )
    limit: int = Field(
        default=10, ge=1, le=100, description='Número de resultados (1-100)'
    )

    @field_validator('query')
    @classmethod
    def clean_query(cls, v: str) -> str:
        """Limpar e normalizar query."""
        return v.strip().lower()

    @field_validator('max_price')
    @classmethod
    def validate_price_range(cls, v: float, info) -> float:
        """Garantir que max_price >= min_price."""
        min_price = info.data.get('min_price', 0)
        if v < min_price:
            raise ValueError('max_price deve ser >= min_price')
        return v


@tool(args_schema=ProductSearchInput)
def search_products(
    query: str,
    category: Optional[str] = None,
    min_price: float = 0,
    max_price: float = 10000,
    sort_by: str = 'relevance',
    limit: int = 10,
) -> str:
    """Buscar produtos no catálogo.

    Args:
        query: Termo de busca.
        category: Categoria do produto.
        min_price: Preço mínimo.
        max_price: Preço máximo.
        sort_by: Ordenação dos resultados.
        limit: Número de resultados.

    Returns:
        Lista de produtos encontrados.
    """
    filters = [f"busca='{query}'"]
    if category:
        filters.append(f'categoria={category}')
    filters.append(f'preço={min_price}-{max_price}')
    filters.append(f'ordenar={sort_by}')
    filters.append(f'limite={limit}')

    return f'Produtos encontrados: [{", ".join(filters)}]'


# =============================================================================
# Exemplo 3: Tipos Complexos (List, Optional)
# =============================================================================


class EmailInput(BaseModel):
    """Schema para envio de e-mail."""

    to: List[str] = Field(min_length=1, description='Lista de destinatários')
    subject: str = Field(
        min_length=1, max_length=200, description='Assunto do e-mail'
    )
    body: str = Field(min_length=1, description='Corpo do e-mail')
    cc: Optional[List[str]] = Field(
        default=None, description='Lista de destinatários em cópia'
    )
    priority: Literal['low', 'normal', 'high'] = Field(
        default='normal', description='Prioridade do e-mail'
    )

    @field_validator('to', 'cc')
    @classmethod
    def validate_emails(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        """Validar formato básico de e-mails."""
        if v is None:
            return v
        for email in v:
            if '@' not in email:
                raise ValueError(f'E-mail inválido: {email}')
        return v


@tool(args_schema=EmailInput)
def send_email(
    to: List[str],
    subject: str,
    body: str,
    cc: Optional[List[str]] = None,
    priority: str = 'normal',
) -> str:
    """Enviar e-mail.

    Args:
        to: Lista de destinatários.
        subject: Assunto do e-mail.
        body: Corpo do e-mail.
        cc: Lista de destinatários em cópia.
        priority: Prioridade (low, normal, high).

    Returns:
        Confirmação de envio.
    """
    cc_count = len(cc) if cc else 0
    return (
        f'✉️ E-mail enviado!\n'
        f'   Para: {len(to)} destinatário(s)\n'
        f'   CC: {cc_count} destinatário(s)\n'
        f'   Assunto: {subject}\n'
        f'   Prioridade: {priority}'
    )


# =============================================================================
# Exemplo 4: Schema com Nested Types
# =============================================================================


class Address(BaseModel):
    """Endereço."""

    street: str = Field(description='Rua e número')
    city: str = Field(description='Cidade')
    state: str = Field(max_length=2, description='Estado (sigla)')
    zip_code: str = Field(pattern=r'^\d{5}-?\d{3}$', description='CEP')


class OrderItem(BaseModel):
    """Item do pedido."""

    product_id: str = Field(description='ID do produto')
    quantity: int = Field(ge=1, le=100, description='Quantidade')
    unit_price: float = Field(ge=0, description='Preço unitário')


class OrderInput(BaseModel):
    """Schema para criação de pedido."""

    customer_id: str = Field(description='ID do cliente')
    items: List[OrderItem] = Field(min_length=1, description='Itens do pedido')
    shipping_address: Address = Field(description='Endereço de entrega')
    notes: Optional[str] = Field(
        default=None, max_length=500, description='Observações'
    )


@tool(args_schema=OrderInput)
def create_order(
    customer_id: str,
    items: List[dict],
    shipping_address: dict,
    notes: Optional[str] = None,
) -> str:
    """Criar um novo pedido.

    Args:
        customer_id: ID do cliente.
        items: Lista de itens do pedido.
        shipping_address: Endereço de entrega.
        notes: Observações opcionais.

    Returns:
        Confirmação do pedido com detalhes.
    """
    total_items = sum(item.get('quantity', 1) for item in items)
    total_value = sum(
        item.get('quantity', 1) * item.get('unit_price', 0) for item in items
    )
    city = shipping_address.get('city', 'N/A')

    return (
        f'📦 Pedido criado!\n'
        f'   Cliente: {customer_id}\n'
        f'   Itens: {total_items}\n'
        f'   Total: R$ {total_value:.2f}\n'
        f'   Entrega: {city}\n'
        f'   Obs: {notes or "Nenhuma"}'
    )


# =============================================================================
# Demonstração
# =============================================================================


async def main():
    """Demonstrar uso das ferramentas com Pydantic."""
    print('🚀 CreateAgents - Exemplos com Pydantic')
    print('=' * 60)

    # Criar agente com todas as ferramentas
    agent = CreateAgent(
        provider='openai',
        model='gpt-5-nano',
        instructions=(
            'Você é um assistente que pode converter temperaturas, '
            'buscar produtos, enviar e-mails e criar pedidos.'
        ),
        tools=[convert_temperature, search_products, send_email, create_order],
        config={'stream': False},
    )

    # Listar ferramentas e seus schemas
    print('\n📋 Ferramentas disponíveis:')
    tools = agent.get_all_available_tools()
    for name, desc in tools.items():
        print(f'   - {name}: {desc[:60]}...')

    # Teste 1: Conversão de temperatura
    print('\n' + '-' * 60)
    print('🌡️  Teste: Conversão de Temperatura')
    response = await agent.chat('Converta 100 graus Fahrenheit para Celsius')
    print(f'   Resposta: {response}')

    # Teste 2: Busca de produtos
    print('\n' + '-' * 60)
    print('🔍 Teste: Busca de Produtos')
    response = await agent.chat(
        'Busque notebooks com preço entre 2000 e 5000 reais, ordenados por avaliação'
    )
    print(f'   Resposta: {response}')

    # Teste 3: Envio de e-mail
    print('\n' + '-' * 60)
    print('✉️  Teste: Envio de E-mail')
    response = await agent.chat(
        'Envie um e-mail de alta prioridade para joao@email.com e maria@email.com '
        "com o assunto 'Reunião urgente' e corpo 'Por favor, confirmar presença'."
    )
    print(f'   Resposta: {response}')

    print('\n' + '=' * 60)
    print('✅ Demonstração concluída!')


# =============================================================================
# Demonstração de Validação
# =============================================================================


def demo_validation():
    """Demonstrar validação Pydantic em ação."""
    print('\n🔍 Demonstração de Validação Pydantic')
    print('=' * 60)

    # Teste de validação bem-sucedida
    print('\n✅ Validação bem-sucedida:')
    try:
        valid_input = ProductSearchInput(
            query='notebook gamer',
            min_price=1000,
            max_price=5000,
            sort_by='price_asc',
            limit=20,
        )
        print(f'   Query: {valid_input.query}')
        print(f'   Preço: {valid_input.min_price} - {valid_input.max_price}')
    except Exception as e:
        print(f'   Erro: {e}')

    # Teste de validação com erro
    print('\n❌ Validação com erro (max_price < min_price):')
    try:
        invalid_input = ProductSearchInput(
            query='notebook',
            min_price=5000,
            max_price=1000,  # Erro: menor que min_price
        )
        print(f'   Resultado: {invalid_input}')
    except Exception as e:
        print(f'   Erro capturado: {type(e).__name__}')

    # Teste de e-mail inválido
    print('\n❌ Validação com erro (e-mail inválido):')
    try:
        invalid_email = EmailInput(
            to=['invalido_sem_arroba'], subject='Teste', body='Corpo'
        )
        print(f'   Resultado: {invalid_email}')
    except Exception as e:
        print(f'   Erro capturado: {type(e).__name__}')

    print('\n' + '=' * 60)


if __name__ == '__main__':
    # Demonstrar validação Pydantic
    demo_validation()

    # Executar demonstração com agente (requer API key)
    print('\n💡 Executando teste com agente...')
    asyncio.run(main())
