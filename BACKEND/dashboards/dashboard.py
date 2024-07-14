import diskcache
from flask import Flask
from dash import Dash
import dash_bootstrap_components as dbc
from dash.long_callback import DiskcacheLongCallbackManager
from dash_bootstrap_templates import load_figure_template

from dashboards.callbacks import register_callbacks
from dashboards.layout import layout

# Initialize cache and long callback manager
cache = diskcache.Cache("./cache")
long_callback_manager = DiskcacheLongCallbackManager(cache)

# Load figure template and external stylesheets
load_figure_template("darkly")
dbc_css = "https://cdn.jsdelivr.net/gh/AnnMarieW/dash-bootstrap-templates/dbc.min.css"

def create_dashboard(server: Flask) -> Flask:
    """Create a comprehensive cryptocurrency analysis dashboard."""
    dash_app = Dash(
        server=server,
        routes_pathname_prefix='/dashboard/',
        external_stylesheets=[dbc.themes.DARKLY, dbc_css],
        long_callback_manager=long_callback_manager,
        suppress_callback_exceptions=True
    )

    # Set the layout for the Dash app
    dash_app.layout = layout

    # Register all callbacks for the Dash app
    register_callbacks(dash_app)

    return server