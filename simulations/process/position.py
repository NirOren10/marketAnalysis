import pandas as pd

class Position:

    def __init__(self,direction,open_time,open_price,enter_reason,status="open"):
        
        self.status = status
        self.direction = direction
        self.open_time = open_time
        self.open_price = open_price
        self.enter_reason = enter_reason
        self.close_time = None
        self.close_price = None
        self.revenue = 0
        self.exit_reason = None
        self.id = f"{direction}_{open_time}"

    def to_dict(self):
        return {
            "direction" : self.direction,
            "status" : self.status,
            "open_time" : self.open_time ,
            "close_time" : self.close_time ,
            "open_price" : self.open_price,
            "close_price" : self.close_price,
            "revenue" : self.revenue,
            "enter_reason" : self.enter_reason,
            "exit_reason" : self.exit_reason
        }
    def ready_to_exit(self,min_pos_time,now):
        return pd.Timedelta(now - self.open_time).total_seconds()/60 >= min_pos_time

    def expired(self,max_pos_time,now):
        return pd.Timedelta(now - self.open_time).total_seconds()/60 >= max_pos_time
    
    def calc_revenue(self):
        print(f"direction: {self.direction};\nopen_price: {self.open_price};\nclose_price: {self.close_price}")
        if self.direction == "buy":
            self.revenue = self.open_price - self.close_price
        elif self.direction == "sell":
            self.revenue = self.close_price - self.open_price
        

        
