import yfinance as yf
import pandas as pd

def fetch_yahoo_finance_stock_data(ticker, start_date, end_date):
    stock = yf.download(ticker, start=start_date, end=end_date)
    if 'Close' not in stock.columns or stock['Close'].empty:
        return pd.Series(dtype=float)
    return stock['Close']
