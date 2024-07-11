from flask import Flask
from dash import Dash, dcc, html
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

        dcc.Tabs(id='tabs', value='tab-arima', children=[
            dcc.Tab(label='ARIMA', value='tab-arima'),
            dcc.Tab(label='Random Forest', value='tab-randomforest'),
            dcc.Tab(label='SARIMAX', value='tab-sarimax')
        ]),

        html.Div(id='tab-content')
    ])

    # Register all callbacks for the Dash app
    register_callbacks(dash_app)

    @dash_app.callback(
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

    @dash_app.callback(
        Output('arima-graph', 'figure'),
        [Input('arima-crypto-dropdown', 'value')]
    )
    def update_arima_graph(selected_crypto):
        # Fetch data
        historical_data = fetch_historical_data([selected_crypto], days=30)
        prices = historical_data[selected_crypto]['Price']
        
        # Apply prediction model
        predictions = get_predictions('arima', prices, '1D')
        
        # Create figure
        figure = go.Figure()
        figure.add_trace(go.Scatter(x=historical_data[selected_crypto]['Date'], y=prices, mode='lines', name='Actual'))
        forecast_dates = pd.date_range(start=historical_data[selected_crypto]['Date'].iloc[-1], periods=31, freq='D')[1:]
        figure.add_trace(go.Scatter(x=forecast_dates, y=predictions, mode='lines', name='Predicted'))
        
        figure.update_layout(title=f'{selected_crypto.capitalize()} Price Prediction using ARIMA',
                             xaxis_title='Date', yaxis_title='Price')
        
        return figure

    @dash_app.callback(
        Output('randomforest-graph', 'figure'),
        [Input('randomforest-crypto-dropdown', 'value')]
    )
    def update_randomforest_graph(selected_crypto):
        # Fetch data
        historical_data = fetch_historical_data([selected_crypto], days=30)
        prices = historical_data[selected_crypto]['Price']
        
        # Apply prediction model
        predictions = get_predictions('random_forest', prices, '1D')
        
        # Create figure
        figure = go.Figure()
        figure.add_trace(go.Scatter(x=historical_data[selected_crypto]['Date'], y=prices, mode='lines', name='Actual'))
        forecast_dates = pd.date_range(start=historical_data[selected_crypto]['Date'].iloc[-1], periods=31, freq='D')[1:]
        figure.add_trace(go.Scatter(x=forecast_dates, y=predictions, mode='lines', name='Predicted'))
        
        figure.update_layout(title=f'{selected_crypto.capitalize()} Price Prediction using Random Forest',
                             xaxis_title='Date', yaxis_title='Price')
        
        return figure

    @dash_app.callback(
        Output('sarimax-graph', 'figure'),
        [Input('sarimax-crypto-dropdown', 'value')]
    )
    def update_sarimax_graph(selected_crypto):
        # Fetch data
        historical_data = fetch_historical_data([selected_crypto], days=30)
        prices = historical_data[selected_crypto]['Price']
        
        # Apply prediction model
        predictions = get_predictions('sarimax', prices, '1D')
        
        # Create figure
        figure = go.Figure()
        figure.add_trace(go.Scatter(x=historical_data[selected_crypto]['Date'], y=prices, mode='lines', name='Actual'))
        forecast_dates = pd.date_range(start=historical_data[selected_crypto]['Date'].iloc[-1], periods=31, freq='D')[1:]
        figure.add_trace(go.Scatter(x=forecast_dates, y=predictions, mode='lines', name='Predicted'))
        
        figure.update_layout(title=f'{selected_crypto.capitalize()} Price Prediction using SARIMAX',
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
