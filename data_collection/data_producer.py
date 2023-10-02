import yfinance as yf
import pandas_market_calendars as mcal
from pprint import pprint
import pandas as pd
import os


start_date = '2023-09-03'
end_date = '2023-10-01'
tickers = ['AAPL','MSFT','AMZN']


# Generate a date range in the interval using pandas
date_interval = [date.strftime('%Y-%m-%d') for date in pd.date_range(start=pd.to_datetime(start_date), end=pd.to_datetime(end_date)+pd.Timedelta(days=1))]



for i in range(len(date_interval)-1):
    date = date_interval[i]
    for ticker in tickers:
        df =yf.download(ticker,  start = date_interval[i] , end = date_interval[i+1], interval="1m")
        if len(df) == 0:
            continue
        folder_path = f"stock_data/{date}"
        if not os.path.exists(folder_path):
            os.mkdir(folder_path)
        df.to_csv(os.path.join(folder_path,f"{ticker}.csv"))

# hst = AP.history(interval="1m",period="1d")
# print(hst.head())
# hst.to_csv("apple1.csv")

# tickers = ["AAPL"] #Subtitute for the tickers you want
# df =yf.download(tickers,  start = "2023-09-05" , end = "2023-09-06", interval="1m")
# df.to_csv("hhhh.csv")