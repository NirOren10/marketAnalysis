from simulations.process.simulation import Simulation
import pandas as pd
import os

start_date = '2023-09-03'
end_date = '2023-10-01'
tickers = ['AAPL','MSFT','AMZN']

date_interval = [date.strftime('%Y-%m-%d') for date in pd.date_range(start=pd.to_datetime(start_date), end=pd.to_datetime(end_date)+pd.Timedelta(days=1))]

data_dates = os.listdir("stock_data")

for date in date_interval:
    if date in data_dates:
        current_date_path = os.path.join("stock_data",date)
        data_tickers = os.listdir(current_date_path)
        
        for ticker in tickers:
            if ticker+".csv" in data_tickers:
                path = os.path.join(current_date_path,ticker)
                sim = Simulation(name=ticker,date=date,config_path=f"simulations/config/{ticker}.json")
                sim.run()