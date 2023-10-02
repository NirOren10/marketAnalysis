import pandas as pd

class Signal:

    def __init__(self,row,config):
        self.row = row
        self.config = config

    def find_signal(self):
        function_list = [func for func in dir(self) if callable(getattr(self, func))]
        # Filter out methods inherited from the base class (e.g., __init__)
        function_list = [func for func in function_list if not func.startswith("__")]

        for name in function_list:
            if name != "find_signal" and hasattr(self, name):
                func = getattr(self, name)
                if callable(func):
                    signal,reason = func()
                    if signal:
                        return signal, reason
                    

    
    def moving_avg_price_deviation(self):
        deviation = (self.row['price'] - self.row['moving_average']) / self.row['moving_average'] * 100
        
        if deviation < -self.config['deviation_threshold']:
            return "buy"
        elif deviation > self.config['deviation_threshold']:
            return "sell"
        else:
            return None

    def moving_avg_crossover(self):
        return None, None
        if (not pd.isna(self.row["short_mov_avg"]) and not pd.isna(self.row["long_mov_avg"])):
            # if row["short_mov_avg"] > row["long_mov_avg"]:
            #     return "buy", "mov_avg_crossover"
            # elif row["short_mov_avg"] < row["long_mov_avg"]:
            #     return "buy", "mov_avg_crossover"
            if self.row["mov_avg_deviation"] > self.config["mov_avg_crossover_deviation_threshold"]:
                return "buy","mov_avg_crossover"
            if self.row["mov_avg_deviation"] < -self.config["mov_avg_crossover_deviation_threshold"]:
                return "sell","mov_avg_crossover"


# if __name__ == "__main__":
#     signal = Signal(row=[],config={})
#     signal.find_signal()