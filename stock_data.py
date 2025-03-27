import yfinance as yf
import pandas as pd

def fetch_yahoo_finance_stock_data(ticker, start_date, end_date):
    #fetching historical stock prices using yfinance
    stock = yf.download(ticker, start = start_date, end = end_date)
    return stock['Close']#retunring only closing prices

data = fetch_yahoo_finance_stock_data("AAPL", "2025-03-01", "2025-03-27")
print(data.head())
