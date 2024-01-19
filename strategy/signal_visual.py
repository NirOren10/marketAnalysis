import pandas as pd
import numpy as np
import os
import json
from datetime import timedelta
import plotly.graph_objects as go


from strategy.signal import Signal
from simulations.process.position import Position

class SingalTester:
    signals = []
    def __init__(self,name,date,config_path):
        path = f"stock_data/{date}/{name}.csv"
        self.data = pd.read_csv(path)
        self.simulation_date = date
        self.config_path = config_path
        self.data_preperation()
        self.import_config()

    def data_preperation(self):
        self.import_config()
        self.data = self.clean(self.data)
        return 

    def import_config(self):
        self.config = json.loads(open(self.config_path,"r").read())
        self.take_profit = self.config["take_profit"]
        self.stop_loss = self.config["stop_loss"]
        self.mov_avg_price_deviation_threshold = self.config["mov_avg_price_deviation_threshold"]
        self.mov_avg_crossover_deviation_threshold = self.config["mov_avg_crossover_deviation_threshold"]
        self.max_pos_time = self.config["max_pos_time"]
        self.std_moving_avg = self.config["moving_average_window"]
        self.long_moving_avg = self.config["long_moving_avg"]
        self.short_moving_avg = self.config["short_moving_avg"]
        self.min_pos_time = self.config['min_position_time']

    def extract_signals(self):
        for index,row in self.data.iterrows():
            direction,signal = Signal(row = row, config=self.config).find_signal()
            if direction != None and signal != None:
                self.signals.append({
                    "direction" : direction,
                    "datetime" : row['datetime'],
                    "reason" : signal
                })

    def graph(self,ind):
        signal = self.signals[ind]
        timewindow = 10 #min
        df_tf = self.data[self.data.datetime >= signal['datetime']-timedelta(minutes=timewindow) & 
                            self.data.datetime <= signal['datetime']+timedelta(minutes=timewindow)]
        hi_pt = df_tf.price.max()
        lo_pt = df_tf.price.min()
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x = df_tf["datetime"],
            y = df_tf["price"],
            name = "price",
            line = dict(color = "blue")
        ))
        fig.add_trace(go.Scatter(
            x = df_tf["datetime"],
            y = df_tf["moving_average"],
            name = "moving_average",
            line = dict(color = "yellow",width = 0.8)
        ))
        fig.add_trace(go.Scatter(
        x = [signal["datetime"]]*2,
        y = [lo_pt,hi_pt],
        name = f"{signal['direction']}",
        line = dict(color = "red" if signal['direction'] == 'sell' else 'green',width = 0.8,dash = "dash")
        ))
        return fig
        

    def clean(self,df):
        df['datetime'] = pd.to_datetime(df["Datetime"])
        df['price'] = df["Close"]
        df.drop(columns=["Datetime","High","Open","Close","Low"],inplace = True)
        df["moving_average"] = self.data["price"].rolling(window=self.std_moving_avg).mean()
        df["short_mov_avg"] = self.data["price"].rolling(window=self.short_moving_avg).mean()
        df["long_mov_avg"] = self.data["price"].rolling(window=self.long_moving_avg).mean()
        df['mov_avg_deviation'] = ((df['short_mov_avg'] - df['long_mov_avg']) / df['long_mov_avg']) * 100

        return df