from dash import Input, Output, dcc, html
import pandas as pd
import plotly.graph_objects as go
from .utilities import fetch_historical_data
from predictive_models.arima import evaluate_arima
from predictive_models.random_forest import evaluate_random_forest
from predictive_models.sarimax import evaluate_sarimax

# dashboards/callbacks.py

def register_callbacks(app):
    @app.callback(
        Output('tab-content', 'children'),
        Input('tabs', 'value')
    )
    def render_tab_content(tab):
        if tab == 'tab-arima':
            return html.Div([
                html.Label("Cryptocurrency"),
                dcc.Dropdown(
                    id='arima-crypto-dropdown',
                    options=[
                        {'label': 'Bitcoin (BTC)', 'value': 'bitcoin'},
                        {'label': 'Ethereum (ETH)', 'value': 'ethereum'},
                        {'label': 'Litecoin (LTC)', 'value': 'litecoin'},
                        {'label': 'Binance Coin (BNB)', 'value': 'binancecoin'},
                        {'label': 'Dogecoin (DOGE)', 'value': 'dogecoin'}
                    ],
                    value='bitcoin'
                ),
                dcc.Graph(id='arima-graph')
            ])
        elif tab == 'tab-randomforest':
            return html.Div([
                html.Label("Cryptocurrency"),
                dcc.Dropdown(
                    id='randomforest-crypto-dropdown',
                    options=[
                        {'label': 'Bitcoin (BTC)', 'value': 'bitcoin'},
                        {'label': 'Ethereum (ETH)', 'value': 'ethereum'},
                        {'label': 'Litecoin (LTC)', 'value': 'litecoin'},
                        {'label': 'Binance Coin (BNB)', 'value': 'binancecoin'},
                        {'label': 'Dogecoin (DOGE)', 'value': 'dogecoin'}
                    ],
                    value='bitcoin'
                ),
                dcc.Graph(id='randomforest-graph')
            ])
        elif tab == 'tab-sarimax':
            return html.Div([
                html.Label("Cryptocurrency"),
                dcc.Dropdown(
                    id='sarimax-crypto-dropdown',
                    options=[
                        {'label': 'Bitcoin (BTC)', 'value': 'bitcoin'},
                        {'label': 'Ethereum (ETH)', 'value': 'ethereum'},
                        {'label': 'Litecoin (LTC)', 'value': 'litecoin'},
                        {'label': 'Binance Coin (BNB)', 'value': 'binancecoin'},
                        {'label': 'Dogecoin (DOGE)', 'value': 'dogecoin'}
                    ],
                    value='bitcoin'
                ),
                dcc.Graph(id='sarimax-graph')
            ])

    @app.callback(
        Output('arima-graph', 'figure'),
        [Input('arima-crypto-dropdown', 'value')]
    )
    def update_arima_graph(selected_crypto):
        # Fetch data
        historical_data = fetch_historical_data([selected_crypto], days=30)
        prices = historical_data[selected_crypto]['Price']
        
        # Apply prediction model
        predictions = evaluate_arima(prices, steps=30)
        
        # Create figure
        figure = go.Figure()
        figure.add_trace(go.Scatter(x=historical_data[selected_crypto]['Date'], y=prices, mode='lines', name='Actual'))
        forecast_dates = pd.date_range(start=historical_data[selected_crypto]['Date'].iloc[-1], periods=31, freq='D')[1:]
        figure.add_trace(go.Scatter(x=forecast_dates, y=predictions, mode='lines', name='Predicted'))
        
        figure.update_layout(title=f'{selected_crypto.capitalize()} Price Prediction using ARIMA',
                             xaxis_title='Date', yaxis_title='Price')
        
        return figure

    @app.callback(
        Output('randomforest-graph', 'figure'),
        [Input('randomforest-crypto-dropdown', 'value')]
    )
    def update_randomforest_graph(selected_crypto):
        # Fetch data
        historical_data = fetch_historical_data([selected_crypto], days=30)
        features = historical_data[selected_crypto][['Date', 'Price']]
        target = historical_data[selected_crypto]['Price']
        
        # Apply prediction model
        predictions, _ = evaluate_random_forest(features, target)
        
        # Create figure
        figure = go.Figure()
        figure.add_trace(go.Scatter(x=historical_data[selected_crypto]['Date'], y=target, mode='lines', name='Actual'))
        forecast_dates = pd.date_range(start=historical_data[selected_crypto]['Date'].iloc[-1], periods=31, freq='D')[1:]
        figure.add_trace(go.Scatter(x=forecast_dates, y=predictions, mode='lines', name='Predicted'))
        
        figure.update_layout(title=f'{selected_crypto.capitalize()} Price Prediction using Random Forest',
                             xaxis_title='Date', yaxis_title='Price')
        
        return figure

    @app.callback(
        Output('sarimax-graph', 'figure'),
        [Input('sarimax-crypto-dropdown', 'value')]
    )
    def update_sarimax_graph(selected_crypto):
        # Fetch data
        historical_data = fetch_historical_data([selected_crypto], days=30)
        prices = historical_data[selected_crypto]['Price']
        
        # Apply prediction model
        predictions = evaluate_sarimax(prices, steps=30)
        
        # Create figure
        figure = go.Figure()
        figure.add_trace(go.Scatter(x=historical_data[selected_crypto]['Date'], y=prices, mode='lines', name='Actual'))
        forecast_dates = pd.date_range(start=historical_data[selected_crypto]['Date'].iloc[-1], periods=31, freq='D')[1:]
        figure.add_trace(go.Scatter(x=forecast_dates, y=predictions, mode='lines', name='Predicted'))
        
        figure.update_layout(title=f'{selected_crypto.capitalize()} Price Prediction using SARIMAX',
                             xaxis_title='Date', yaxis_title='Price')
        
        return figure

def get_predictions(model_name, data, target):
    if model_name == 'arima':
        return evaluate_arima(data, steps=30)
    elif model_name == 'sarimax':
        return evaluate_sarimax(data, steps=30)
    elif model_name == 'random_forest':
        return evaluate_random_forest(data, target)
    else:
        raise ValueError("Unknown model")
