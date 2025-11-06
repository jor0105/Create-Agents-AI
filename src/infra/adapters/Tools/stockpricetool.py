from src.domain import BaseTool
from src.infra.config.logging_config import LoggingConfig


class StockPriceTool(BaseTool):
    """Fictitious stock price lookup tool for testing purposes.

    Simulates fetching stock prices from B3 (Brazilian stock exchange).
    In a real implementation, this would integrate with a financial API
    like Yahoo Finance, Alpha Vantage, or B3's official API.
    """

    name = "get_stock_price"
    description = (
        "Use this tool to obtain the most recent closing price for a Brazilian "
        "stock (B3). The input should be the ticker symbol (e.g., 'PETR4', 'VALE3')."
    )
    parameters = {
        "type": "object",
        "properties": {
            "ticker": {
                "type": "string",
                "description": "The stock ticker symbol from B3 (e.g., 'PETR4', 'VALE3')",
            }
        },
        "required": ["ticker"],
    }

    def __init__(self):
        """Initialize the StockPriceTool with logging."""
        self.__logger = LoggingConfig.get_logger(__name__)

    def execute(self, ticker: str) -> str:
        """Execute a simulated stock price lookup.

        Args:
            ticker: The stock ticker symbol (e.g., 'PETR4').

        Returns:
            A string with the stock price or an error message.
        """
        self.__logger.info(f"Executing stock price lookup for ticker: '{ticker}'")

        # Simulated database of stock prices
        db_prices = {
            "PETR4": 38.50,
            "VALE3": 65.10,
            "ITUB4": 32.20,
            "BBDC4": 15.80,
            "ABEV3": 12.45,
        }

        ticker_upper = ticker.upper()
        price = db_prices.get(ticker_upper)

        if price is not None:
            result = f"Observation: The most recent closing price for {ticker_upper} is R$ {price:.2f}."
            self.__logger.debug(f"Stock price found: {ticker_upper} = R$ {price:.2f}")
            return result
        else:
            result = f"Observation: Ticker symbol '{ticker_upper}' not found in the database. Available tickers: {', '.join(db_prices.keys())}."
            self.__logger.warning(f"Stock ticker not found: {ticker_upper}")
            return result
