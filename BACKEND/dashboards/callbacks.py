from dash import Input, Output, dcc, html
import pandas as pd
import plotly.graph_objects as go
from predictive_models.arima import evaluate_arima
from predictive_models.random_forest import evaluate_random_forest
from predictive_models.sarimax import evaluate_sarimax
from .utilities import fetch_historical_data

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
        historical_data = fetch_historical_data([selected_crypto], days=30)
        prices = historical_data[selected_crypto]
        predictions = evaluate_arima(prices, steps=30)
        figure = go.Figure()
        figure.add_trace(go.Scatter(x=prices.index, y=prices, mode='lines', name='Actual'))
        forecast_dates = pd.date_range(start=prices.index[-1], periods=30, freq='D')
        figure.add_trace(go.Scatter(x=forecast_dates, y=predictions, mode='lines', name='Predicted'))
        figure.update_layout(title=f'{selected_crypto.capitalize()} Price Prediction using ARIMA', xaxis_title='Date', yaxis_title='Price')
        return figure

    @app.callback(
        Output('randomforest-graph', 'figure'),
        [Input('randomforest-crypto-dropdown', 'value')]
    )
    def update_randomforest_graph(selected_crypto):
        historical_data = fetch_historical_data([selected_crypto], days=30)
        prices = historical_data[selected_crypto]
        features = pd.DataFrame(prices).reset_index()
        # Drop the datetime column if it exists, otherwise do nothing
        if 'index' in features.columns:
            features = features.drop(columns=['index'])
        target = prices.values
        predictions, _ = evaluate_random_forest(features, target)
        figure = go.Figure()
        figure.add_trace(go.Scatter(x=prices.index, y=target, mode='lines', name='Actual'))
        forecast_dates = pd.date_range(start=prices.index[-1], periods=30, freq='D')
        figure.add_trace(go.Scatter(x=forecast_dates, y=predictions, mode='lines', name='Predicted'))
        figure.update_layout(title=f'{selected_crypto.capitalize()} Price Prediction using Random Forest', xaxis_title='Date', yaxis_title='Price')
        return figure

    @app.callback(
        Output('sarimax-graph', 'figure'),
        [Input('sarimax-crypto-dropdown', 'value')]
    )
    def update_sarimax_graph(selected_crypto):
        historical_data = fetch_historical_data([selected_crypto], days=30)
        prices = historical_data[selected_crypto]
        predictions = evaluate_sarimax(prices, steps=30)
        figure = go.Figure()
        figure.add_trace(go.Scatter(x=prices.index, y=prices, mode='lines', name='Actual'))
        forecast_dates = pd.date_range(start=prices.index[-1], periods=30, freq='D')
        figure.add_trace(go.Scatter(x=forecast_dates, y=predictions, mode='lines', name='Predicted'))
        figure.update_layout(title=f'{selected_crypto.capitalize()} Price Prediction using SARIMAX', xaxis_title='Date', yaxis_title='Price')
        return figure
