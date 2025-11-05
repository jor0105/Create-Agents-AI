from src.domain import BaseTool


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

    def execute(self, ticker: str) -> str:
        """Execute a simulated stock price lookup.

        Args:
            ticker: The stock ticker symbol (e.g., 'PETR4').

        Returns:
            A string with the stock price or an error message.
        """
        print(f"[StockPriceTool] Looking up price for: {ticker}")

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
            return f"Observation: The most recent closing price for {ticker_upper} is R$ {price:.2f}."
        else:
            return f"Observation: Ticker symbol '{ticker_upper}' not found in the database. Available tickers: {', '.join(db_prices.keys())}."
