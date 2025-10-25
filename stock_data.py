import yfinance as yf
from yfinance.exceptions import YFRateLimitError
import pandas as pd

def fetch_yahoo_finance_stock_data(ticker, start_date, end_date):
    #fetching historical stock prices using yfinance
    
    try:
        stock = yf.download(ticker, start = start_date, end = end_date, auto_adjust=False)
    except YFRateLimitError:
         if 'Close' not in stock.columns or stock['Close'].empty:
            return pd.Series(dtype=float) #empty Series
    
    return stock['Close']#retunring only closing prices
