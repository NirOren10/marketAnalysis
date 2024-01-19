import pandas as pd
import numpy as np
import os
import json
from datetime import timedelta

from strategy.signal import Signal
from simulations.process.position import Position

class Simulation:

    in_position = False
    positions = []
    orders = []
    revenue = 0

    def __init__(self,name,date,config_path, balance=1000):
        path = f"stock_data/{date}/{name}.csv"
        self.data = pd.read_csv(path)
        self.simulation_name = name
        self.simulation_date = date
        self.config_path = config_path
        self.balance = balance

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

    def run_simulation1(self):
        self.positions = []
        self.orders = []
        last_enterance_datetime = None
        for index,row in self.data.iterrows():
            direction,signal = Signal(row = row, config=self.config).find_signal()

            if not self.in_position:
                # direction,signal = self.check_signal(row)
                if signal != None:
                    print(f"\nEntering, {direction},{ row['datetime']}")
                    self.enter_position(direction,signal,row)
                    last_enterance_datetime = row['datetime']
            else:
                if index == self.data.index[-1]:
                    self.execute_exit(row,"last_row")

                # checking if minimum position time has passed
                elif pd.Timedelta(row.datetime - last_enterance_datetime).total_seconds()/60 > self.min_pos_time:
                    if signal is not None:
                        pass
                    else:
                        self.check_position_exit(row)
            
        return

    def run_simulation(self):
        self.positions = []
        self.orders = []

        for index,row in self.data.iterrows():
            direction,signal = Signal(row = row, config=self.config).find_signal()
            if index == self.data.index[-1]:
                self.exit_all(row) #TODO

            self.check_basic_exist(row)

            if signal != None:
                print(f"\nEntering, {direction},{row['datetime']}")
                self.enter_position(direction,signal,row)
            
        return


    def check_signal(self,row):
        if self.check_moving_ave(row,self.deviation_threshold) != None:
            return self.check_moving_ave(row,self.deviation_threshold), "moving_average"
        return None, None

    def check_basic_exist(self,row):
        # TODO: Add min exit time
        for position in [i for i in self.positions if i.status == "open"]:
            if position.direction == "buy":
                if (row["price"] - position.open_price) > self.take_profit:
                    self.exit_position(position,row,"take_profit")
                elif (row["price"] - position.open_price) < self.stop_loss:
                    self.exit_position(position,row,"stop_loss")
                elif position.expired(self.max_pos_time,row["datetime"]):
                    self.exit_position(position,row,"max_pos_time")

            if position.direction == "sell":
                if (position.open_price - row["price"]) > self.take_profit:
                    self.exit_position(position,row,"take_profit")
                elif (position.open_price - row["price"]) < self.stop_loss:
                    self.exit_position(position,row,"stop_loss")
                elif position.expired(self.max_pos_time,row["datetime"]):
                    self.exit_position(position,row,"max_pos_time")

    def exit_all(self,row):
        for position in [i for i in self.positions if i.status == "open"]:
            self.exit_position(position,row,"end_of_file")

    def exit_position(self,position,row,reason):
        position.close_time = row['datetime']
        position.close_price = row['price']
        position.exit_reason = reason
        position.status = "closed"
        position.calc_revenue()
        self.revenue += position.revenue
    
    def enter_position(self,direction,signal,row):
        if self.balance >= row["price"] and direction == "buy":
            self.balance-=row["price"]
            self.orders.append({
                "direction" : direction,
                "datetime" : row["datetime"],
                "price" : row["price"],
                "signal" : signal,
                "new_balance" : self.balance
            })
            self.positions.append(
                Position(direction=direction,
                        open_price=row["price"],
                        open_time=row["datetime"],
                        enter_reason=signal)
            )
        elif direction == "sell":
            self.balance+=row["price"]
            self.orders.append({
                "direction" : direction,
                "datetime" : row["datetime"],
                "price" : row["price"],
                "signal" : signal,
                "new_balance" : self.balance
            })
            self.positions.append(
                Position(direction=direction,
                        open_price=row["price"],
                        open_time=row["datetime"],
                        enter_reason=signal)
            )
        else:
            self.positions.append(
                Position(direction=direction,
                        open_price=row["price"],
                        open_time=row["datetime"],
                        enter_reason="insufficient_balance",
                        status="insufficient_balance"
                        )
            )
            print(f'Insufficient balance for Buy. Price: {row["price"]}. ')

    def check_position_exit(self,row,order):
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
        if self.smart_exit():
            self.execute_exit(row,"smart_exit")
            return

        # Max Position Time
        if pd.Timedelta(row['datetime']-enter_order['datetime']).total_seconds()/60 >= self.max_pos_time:
            print('max time hit:', pd.Timedelta(row['datetime']-enter_order['datetime']).total_seconds()/60)
            self.execute_exit(row,"max_position_time")
            return

    def execute_exit(self,row,exit_reason,order):
        enter_order = order
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
        
        pd.DataFrame([i.to_dict() for i in self.positions]).to_csv(os.path.join(folder_path,"positions.csv"),index=False)
        pd.DataFrame(self.orders).to_csv(os.path.join(folder_path,"orders.csv"),index=False)

    def run(self):
        self.data_preperation()
        self.run_simulation()
        self.save_outputs()

        if len(self.positions)>0:
            print("REVENUE:", pd.DataFrame([i.to_dict() for i in self.positions])["revenue"].sum())
        else:
            print("NO POSITIONS")

if __name__ == "__main__":
    sim = Simulation("AAPL","2023-09-13","simulations/config/AAPL.json")
    sim.run()