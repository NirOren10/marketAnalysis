import plotly.graph_objects as go
import plotly
import pandas as pd
import datetime

def graph_position(data, position):
    start = pd.to_datetime(position["enter_datetime"]) - pd.Timedelta(minutes=20)
    end = pd.to_datetime(position["exit_datetime"]) + pd.Timedelta(minutes=20)
    df = data[(data.datetime >= start) & (data.datetime <= end)]
    enter_clr = "green" if position['direction'] == "buy" else "red"
    exit_clr = "red" if position['direction'] == "buy" else "green"

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
        x = [position["enter_datetime"]]*2,
        y = [lo_pt,hi_pt],
        name = f"enter @ {position['enter_price']}",
        line = dict(color = enter_clr,width = 0.8,dash = "dash")
    ))

    fig.add_trace(go.Scatter(
        x = [position["exit_datetime"]]*2,
        y = [lo_pt,hi_pt],
        name = f"exit @ {position['exit_price']}",
        line = dict(color = exit_clr,width = 0.8,dash = "dash")
    ))

    fig.add_annotation(
            text=f'''
direction: {position['direction']} <br>
revenue: {round(position['revenue'],7)} <br>
enter_reason: {position['enter_reason']} <br>
exit_reason: {position['exit_reason']} <br>
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
