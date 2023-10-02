import pandas as pd
import numpy as np
import os
import json
from datetime import timedelta

from strategy.signal import Signal

class Simulation:
    in_position = False
    positions = []
    orders = []
    revenue = 0
    simulation_name = None
    simulation_date = None

    def __init__(self,name,date,config_path):
        path = f"stock_data/{date}/{name}.csv"
        self.data = pd.read_csv(path)
        self.simulation_name = name
        self.simulation_date = date
        self.config_path = config_path


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

    def run_simulation(self):
        for index,row in self.data.iterrows():
            direction,signal = Signal(row = row, config=self.config).find_signal()
            if not self.in_position:
                # direction,signal = self.check_signal(row)
                if signal != None:
                    print(f"\nEntering, {direction},{ row['datetime']}")
                    self.enter_position(direction,signal,row)
            else:
                if index == self.data.index[-1]:
                    self.execute_exit(row,"last_row")
                else:
                    self.check_position_exit(row)
        return

    def check_signal(self,row):
        if self.check_moving_ave(row,self.deviation_threshold) != None:
            return self.check_moving_ave(row,self.deviation_threshold), "moving_average"
        return None, None

    def enter_position(self,direction,signal,row):
        self.in_position = True
        self.orders.append({
            "direction" : direction,
            "datetime" : row["datetime"],
            "price" : row["price"],
            "signal" : signal
        })

    def check_position_exit(self,row):
        enter_order = self.orders[-1]

        # Take Profit
        if enter_order['direction'] == "buy":
            if row["price"] - enter_order["price"] >= self.take_profit:
                self.execute_exit(row,"take_profit")
                return
        elif enter_order['direction'] == "sell":
            if enter_order["price"] - row["price"] >= self.take_profit:
                self.execute_exit(row,"take_profit")
                return

        # Stop Loss
        if enter_order['direction'] == "buy":
            if row["price"] - enter_order["price"] <= self.stop_loss:
                self.execute_exit(row,"stop_loss")
                return
        elif enter_order['direction'] == "sell":
            if enter_order["price"] - row["price"] <= self.stop_loss:
                self.execute_exit(row,"stop_loss")
                return

        # Smart Exit
        elif self.smart_exit():
            self.execute_exit(row,"smart_exit")
            return

        # Max Position Time
        elif pd.Timedelta(row['datetime']-enter_order['datetime']).total_seconds()/60 >= self.max_pos_time:
            self.execute_exit(row)
            return
 
    def execute_exit(self,row,exit_reason):
        enter_order = self.orders[-1]
        profit = row["price"] - enter_order["price"] if enter_order['direction'] == "buy" else enter_order["price"] - row["price"]

        self.positions.append({
            "enter_datetime" : enter_order["datetime"],
            "exit_datetime" : row["datetime"],
            "enter_price" : enter_order["price"],
            "exit_price" : row["price"],
            "direction" : enter_order['direction'],
            "revenue" : profit,
            "enter_reason" : enter_order["signal"],
            "exit_reason" : exit_reason
        })

        self.orders.append({
            "direction" : "buy" if enter_order["direction"]=="sell" else "sell",
            "datetime" : row["datetime"],
            "price" : row["price"],
            "signal" : exit_reason
        })
        self.in_position = False

        return 

    def smart_exit(self):
        return False

    def clean(self,df):
        df['datetime'] = pd.to_datetime(df["Datetime"])
        df['price'] = df["Close"]
        df.drop(columns=["Datetime","High","Open","Close","Low"],inplace = True)
        df["moving_average"] = self.data["price"].rolling(window=self.std_moving_avg).mean()
        df["short_mov_avg"] = self.data["price"].rolling(window=self.short_moving_avg).mean()
        df["long_mov_avg"] = self.data["price"].rolling(window=self.long_moving_avg).mean()
        df['mov_avg_deviation'] = ((df['short_mov_avg'] - df['long_mov_avg']) / df['long_mov_avg']) * 100

        return df

    def save_outputs(self):
        folder_path = f"simulations_results/{self.simulation_date}/{self.simulation_name}"
        if not os.path.exists(f"simulations_results/{self.simulation_date}"):
            os.mkdir(f"simulations_results/{self.simulation_date}")
        
        if not os.path.exists(folder_path):
            os.mkdir(folder_path)
        
        pd.DataFrame(self.positions).to_csv(os.path.join(folder_path,"positions.csv"),index=False)
        pd.DataFrame(self.orders).to_csv(os.path.join(folder_path,"orders.csv"),index=False)

    def run(self):
        self.data_preperation()
        self.run_simulation()
        self.save_outputs()

        if len(self.positions)>0:
            print("REVENUE:", pd.DataFrame(self.positions)["revenue"].sum())
        else:
            print("NO POSITIONS")

if __name__ == "__main__":
    sim = Simulation("AAPL","2023-09-13","simulations/config/AAPL.json")
    sim.run()