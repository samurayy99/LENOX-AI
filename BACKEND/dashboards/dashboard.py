from flask import Flask
from dash import Dash, dcc, html, dash_table
from dash.dependencies import Input, Output
import plotly.graph_objs as go
import pandas as pd
from dashboards.callbacks import register_callbacks, get_predictions
from metrics.metrics import rmse, mae, accuracy_score
from dashboards.utilities import fetch_historical_data

def create_dashboard(server: Flask) -> Flask:
    """Create a comprehensive cryptocurrency analysis dashboard."""
    dash_app = Dash(server=server, routes_pathname_prefix='/dashboard/')

    # Define the layout for the Dash app
    dash_app.layout = html.Div([
        html.H1("CryptoMaster Ultimate Dashboard", style={'textAlign': 'center'}),

        dcc.Tabs(id='tabs', value='tab-predictive', children=[
            dcc.Tab(label='Market Overview', value='tab-market'),
            dcc.Tab(label='Comparative Analysis', value='tab-comparative'),
            dcc.Tab(label='Historical Data Analysis', value='tab-historical'),
            dcc.Tab(label='Predictive Analytics', value='tab-predictive'),
            dcc.Tab(label='Technical Analysis', value='tab-technical'),
            dcc.Tab(label='Dynamic Visualization', value='tab-dynamic')
        ]),

        html.Div(id='tab-content', children=[
            html.Label("Prediction Model"),
            dcc.Dropdown(
                id='model-dropdown',
                options=[
                    {'label': 'ARIMA', 'value': 'arima'},
                    {'label': 'SARIMAX', 'value': 'sarimax'},
                    {'label': 'Random Forest', 'value': 'random_forest'}
                ],
                value='arima'
            ),

            html.Label("Timeframe"),
            dcc.Dropdown(
                id='timeframe-dropdown',
                options=[
                    {'label': '1 Day', 'value': '1D'},
                    {'label': '1 Week', 'value': '1W'},
                    {'label': '1 Month', 'value': '1M'},
                    {'label': '1 Year', 'value': '1Y'}
                ],
                value='1D'
            ),

            html.Label("Cryptocurrency"),
            dcc.Dropdown(
                id='crypto-dropdown',
                options=[
                    {'label': 'Bitcoin (BTC)', 'value': 'bitcoin'},
                    {'label': 'Ethereum (ETH)', 'value': 'ethereum'},
                    {'label': 'Litecoin (LTC)', 'value': 'litecoin'},
                    {'label': 'Binance Coin (BNB)', 'value': 'binancecoin'},
                    {'label': 'Dogecoin (DOGE)', 'value': 'dogecoin'}
                ],
                value='bitcoin'
            ),

            dcc.Graph(id='prediction-graph')
        ])
    ])

    # Register all callbacks for the Dash app
    register_callbacks(dash_app)

    @dash_app.callback(
        Output('prediction-graph', 'figure'),
        [Input('model-dropdown', 'value'),
         Input('timeframe-dropdown', 'value'),
         Input('crypto-dropdown', 'value')]
    )
    def update_graph(selected_model, selected_timeframe, selected_crypto):
        # Fetch data
        historical_data = fetch_historical_data([selected_crypto], days=30)
        prices = historical_data[selected_crypto]['Price']
        
        # Apply prediction model
        predictions = get_predictions(selected_model, prices, selected_timeframe)
        
        # Create figure
        figure = go.Figure()
        figure.add_trace(go.Scatter(x=historical_data[selected_crypto]['Date'], y=prices, mode='lines', name='Actual'))
        forecast_dates = pd.date_range(start=historical_data[selected_crypto]['Date'].iloc[-1], periods=31, freq='D')[1:]
        figure.add_trace(go.Scatter(x=forecast_dates, y=predictions, mode='lines', name='Predicted'))
        
        figure.update_layout(title=f'{selected_crypto.capitalize()} Price Prediction using {selected_model.upper()}',
                             xaxis_title='Date', yaxis_title='Price')
        
        return figure

    return server


def evaluate_predictions(predictions, targets):
    rmse_value = rmse(predictions, targets)
    mae_value = mae(predictions, targets)
    accuracy = accuracy_score(predictions, targets)

    # Return or store results for further visualization
    return {
        "rmse": rmse_value,
        "mae": mae_value,
        "accuracy": accuracy
    }
