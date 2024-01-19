import plotly.graph_objects as go
import plotly
import pandas as pd
import datetime

def graph_day(df):
    # start = pd.to_datetime(position["enter_datetime"]) - pd.Timedelta(minutes=20)
    # end = pd.to_datetime(position["exit_datetime"]) + pd.Timedelta(minutes=20)
    # df = data[(data.datetime >= start) & (data.datetime <= end)]



    hi_pt = df.price.max()
    lo_pt = df.price.min()

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x = df["datetime"],
        y = df["price"],
        name = "price",
        line = dict(color = "blue")
    ))
    fig.add_trace(go.Scatter(
        x = df["datetime"],
        y = df["moving_average"],
        name = "moving_average",
        line = dict(color = "yellow",width = 0.8)
    ))
    fig.add_trace(go.Scatter(
        x = df["datetime"],
        y = df["long_mov_avg"],
        name = "long_mov_avg",
        line = dict(color = "green",width = 0.8)
    ))

    

    fig.add_annotation(
            text=f'''
                DAY GRAPH
                ''',
            align='left',
            showarrow=False,
            xref='paper',
            yref='paper',
            x=1.0,
            y=1.1,
            bordercolor='black',
            borderwidth=1)
    return fig
