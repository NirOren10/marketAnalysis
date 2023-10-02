from dash import Dash, html, dcc, callback, Output, Input, State
from dash.dash_table.Format import Group
import plotly.graph_objects as go
import pandas as pd
import dash_table
from strategy.moving_ave import trading_strategy
import plotly.io as pio

df = pd.read_csv('apple.csv')
df.Datetime = pd.to_datetime(df.Datetime)
df["date"] = df["Datetime"].dt.day

app = Dash(__name__)

app.layout = html.Div([
    html.H1(children='Title of Dash App', style={'textAlign':'center'}),
    dcc.Dropdown(options=[{'label': str(date), 'value': date} for date in df.date.unique()], value=list(df.date.unique())[0], id='date-selection'),
    dcc.Dropdown(options=[{"label": "None", "value": "None"}, {"label": "Moving Ave", "value": "Moving Ave"}], value="None", id='strategy-selection'),
    dcc.Checklist(
        id='selection-checkboxes',  # Unique ID for the component
        options=[
            {'label': 'show Moving Ave', 'value': 'show Moving Ave'},  # List of options with labels and values
            {'label': 'Option 2', 'value': 'option2'},
            {'label': 'Option 3', 'value': 'option3'}
        ],
        value=['option1', 'option2'],  # Default selected options (if any)
        labelStyle={'display': 'block'}  # Display options in separate lines
    ),
    html.P(children='Window Size'),
    dcc.Input(value=5, id='window-size', type="number"),
    html.P(children='Deviation'),
    dcc.Input(value=5, id='deviation', type="number"),
    html.Button("Simulate", id="sim-btn"),
    dcc.Graph(id='graph-content'),
    # dcc.Graph(id='graph-content2'),
    html.Div(id='output-message'),
    html.Div(id='positions-list', children=[]),
    dash_table.DataTable(
        id='positions-table',
        columns=[
            {'name': 'Direction', 'id': 'direction'},
            {'name': 'Datetime', 'id': 'datetime'},
            {'name': 'Price', 'id': 'price'},
        ],
    ),
])

@app.callback(
    Output('graph-content', 'figure', allow_duplicate=True),
    Input('date-selection', 'value'),
    Input("strategy-selection", "value"),
    Input("window-size", "value"),
    Input("selection-checkboxes","value"),
    prevent_initial_call=True  # Add this line to prevent initial callback
)
def selectday(date, strategy, window_size,selected_shows):
    print(selected_shows)
    fig = go.Figure()
    dff = df[df.date == date]
    if "show Moving Ave" in selected_shows and window_size is not None and window_size > 0:
        dff["movingAve"] = dff.Close.rolling(window=window_size).mean()
        fig.add_trace(go.Scatter(
            x=dff['Datetime'],
            y=dff["movingAve"],
            line=dict(color="red"),
            name="Moving Ave"
        ))
    
    fig.add_trace(go.Scatter(
        x=dff['Datetime'],
        y=dff["Close"],
        line=dict(color="blue"),
            name="Price"
    ))
    return fig

@app.callback(
    [Output('output-message', 'children'),
     Output('positions-table', 'data'),
     Output('graph-content', 'figure')],
    Input('sim-btn', 'n_clicks'),
    State('date-selection', 'value'),
    State('deviation', 'value'),
    State("window-size", "value"),
    State('graph-content', 'figure')
)
def runsim(n_clicks, date, deviation, window_size,graph):
    if n_clicks is None:
        return "Start Simulation to see results", [], go.Figure()

    final_capital, positions = trading_strategy(df[df.date == date], deviation, window_size)
    positions_html = []
    for direction, datetime, price in positions:
        positions_html.append(html.Tr([html.Td(direction), html.Td(datetime), html.Td(price)]))
    positions_data = [{'direction': direction, 'datetime': datetime, 'price': price} for direction, datetime, price in positions]
    # print(graph)

    fig = go.Figure(graph)
    dff = df[df.date == date]

    fig.add_trace(go.Scatter(
        x=dff['Datetime'],
        y=dff["Close"],
        line=dict(color="blue"),
        name="Close Price"
    ))

    # Add scatter traces for each position
    for position in positions_data:
        if position['direction'] == 'buy':
            marker_color = 'green'
        else:
            marker_color = 'red'

        fig.add_trace(go.Scatter(
            x=[position['datetime']]*3,
            y=[dff.Close.min(),position['price'],dff.Close.max()],
            mode='markers+lines',
            legendgroup=position['direction'],
            marker=dict(size=2, color=marker_color),
            line= dict(color=marker_color,dash="dash",width=1),
            name=f'{position["direction"]} Position'
        ))
    return f"DONE: {final_capital:.2f}", positions_data, fig

if __name__ == '__main__':
    app.run(debug=True)
