import yfinance as yf
import pandas as pd

def fetch_yahoo_finance_stock_data(ticker, start_date, end_date):
    #fetching historical stock prices using yfinance
    stock = yf.download(ticker, start = start_date, end = end_date)
    
    #ensuring the 'close' column exists and is not empty
    if 'Close' not in stock.columns or stock['Close'].empty:
        return pd.Series(dtype=float) #empty Series
    
    return stock['Close']#retunring only closing prices
