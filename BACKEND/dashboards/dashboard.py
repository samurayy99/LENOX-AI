from flask import Flask
from dash import Dash, dcc, html

from dashboards.callbacks import register_callbacks

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

    return server
