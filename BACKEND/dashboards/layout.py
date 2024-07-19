from dash import html, dcc
import dash_bootstrap_components as dbc

from dashboards.components.info_card import info_card
from dashboards.components.overview_card import overview_card
from dashboards.components.details_cards import bitcoin_card, altcoin_card
from dashboards.components.table_cards import trend_card, pump_card

# Main layout of the dashboard
layout = html.Div([
    dcc.Store(id="timestamp", data=0),  # Timestamp of most recent update
    dcc.Store(id="altcoin", data=""),   # Which altcoin is currently selected
    dcc.Store(id='zoom-script', storage_type='local', data=''),
    dbc.Container([
        dbc.Row(dbc.Col(info_card, width=12)),
        html.Br(),
        dbc.Row([
            dbc.Col([
                dbc.Row([
                    dbc.Col(overview_card, width=12, lg=6, className="mb-3"),
                    dbc.Col(bitcoin_card, width=12, lg=6, className="mb-3"),
                ]),
                dbc.Row(dbc.Col(altcoin_card, width=12, className="mb-3")),
            ], width=12, lg=6),
            dbc.Col([
                dbc.Row(dbc.Col(trend_card, width=12, className="mb-3")),
                dbc.Row(dbc.Col(pump_card, width=12, className="mb-3")),
            ], width=12, lg=6),
        ]),
        html.Br(),
        dbc.Row(dbc.Col(html.A("Back to Chat", href="/", className="btn btn-primary"), width=12, className="text-center")),
    ], fluid=True, className="dashboard-container"),
], className="dashboard-wrapper")