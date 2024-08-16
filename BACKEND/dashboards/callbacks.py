import os
import time
import pandas as pd
from datetime import datetime
import logging
import requests

from dash import Dash, no_update, ctx, Output, Input, State
import dash_bootstrap_components as dbc
from dash.exceptions import PreventUpdate

from dashboards.market_data import update_market_data
from dashboards.components.table_cards import get_row_highlight_condition
from dashboards.components.figures import get_candlestick_figure, get_bar_figure
from dashboards.utils import filter_df, add_emas

# Set up logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def register_callbacks(app: Dash):
    logger.info("Registering callbacks")

    @app.long_callback(
    Output("timestamp", "data"),
    Input("update_button", "n_clicks"),
    running=[
        (Output("update_button", "disabled"), True, False),
        (Output("update_button", "children"), [dbc.Spinner(size="sm"), " Updating..."], "Update Data"),
    ],
        timeout=300000  # 5 minutes in milliseconds
    )
    def update_data(n_clicks):
        logger.info(f"update_data callback triggered with n_clicks: {n_clicks}")
        timestamp = int(time.time())
        logger.debug(f"Updating market data at timestamp: {timestamp}")
        max_retries = 3
        retry_delay = 5  # seconds

        for attempt in range(max_retries):
            try:
                update_market_data()
                logger.info("Market data updated successfully")
                return timestamp
            except requests.exceptions.RequestException as e:
                logger.error(f"Error updating market data (attempt {attempt + 1}/{max_retries}): {str(e)}")
                if attempt < max_retries - 1:
                    logger.info(f"Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                else:
                    logger.error("Max retries reached. Unable to update market data.")
                    raise

    @app.callback(
        Output("last_update_text", "children"),
        Input("timestamp", "data"),
        prevent_initial_call=True,
    )
    def set_last_update_text(timestamp):
        logger.info(f"set_last_update_text callback triggered with timestamp: {timestamp}")
        last_update_text = f"Last update: {datetime.fromtimestamp(timestamp).strftime('%d.%m.%Y, %H:%M')}"
        logger.debug(f"Setting last update text: {last_update_text}")
        return last_update_text

    @app.callback(
        Output("trend_table", "data"),
        Input("timestamp", "data"),
        Input("radio_trend", "value"),
        prevent_initial_call=True,
    )
    def update_trend_table(timestamp, filter):
        logger.info(f"update_trend_table callback triggered with timestamp: {timestamp}, filter: {filter}")
        try:
            df = pd.read_csv(os.path.join("data", "market_data.csv"), index_col="name")
            logger.debug(f"DataFrame columns: {df.columns}")
            logger.debug(f"DataFrame shape before processing: {df.shape}")

            df = df.drop(["BTC"])
            df["id"] = df.index

            required_columns = ["id", "trend_strength", "gain_1d", "gain_1w", "gain_1m"]
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                logger.error(f"Missing columns in market_data.csv: {missing_columns}")
                return []

            df = filter_df(df, filter)
            logger.debug(f"DataFrame shape after filtering: {df.shape}")

            df = df[required_columns]
            
            if df.empty:
                logger.warning("DataFrame is empty after filtering")
                return []
            
            data = df.to_dict(orient="records")
            logger.debug(f"First 5 records of data to be returned: {data[:5]}")
            return data
        except Exception as e:
            logger.error(f"Error in update_trend_table: {str(e)}")
            return []

    @app.callback(
        Output("pump_table", "data"),
        Input("timestamp", "data"),
        Input("radio_pump", "value"),
        prevent_initial_call=True,
    )
    def update_pump_table(timestamp, filter):
        logger.info(f"update_pump_table callback triggered with timestamp: {timestamp}, filter: {filter}")
        try:
            df = pd.read_csv(os.path.join("data", "market_data.csv"), index_col="name")
            logger.debug(f"Read {len(df)} rows from market_data.csv for pump table")
            df = df.drop(["BTC"])
            df["id"] = df.index
            df = filter_df(df, filter)
            df = df.loc[df["pump_strength"] > 2]
            df = df[["id", "pump_strength", "gain_1d", "gain_1w", "gain_1m"]]   
            df = df.sort_values(by=["pump_strength"], ascending=False)
            logger.debug(f"Filtered pump table data shape: {df.shape}")
            return df.to_dict("records")
        except Exception as e:
            logger.error(f"Error in update_pump_table: {str(e)}")
            return []

    @app.callback(
        Output("trend_table", "page_current"),
        Output("pump_table", "page_current"),
        Input("timestamp", "data"),
        Input("trend_table", "sort_by"),
    )
    def reset_to_first_page(timestamp, sort_by):
        logger.info(f"reset_to_first_page callback triggered with timestamp: {timestamp}, sort_by: {sort_by}")
        if ctx.triggered_id == "timestamp":
            logger.debug("Resetting both tables to first page")
            return 0, 0
        logger.debug("Resetting only trend table to first page")
        return 0, no_update

    @app.callback(
        Output("altcoin", "data"),
        Output("trend_table", "active_cell"), Output("trend_table", "selected_cells"), Output("trend_table", "style_data_conditional"),
        Output("pump_table", "active_cell"), Output("pump_table", "selected_cells"), Output("pump_table", "style_data_conditional"),
        Input("trend_table", "active_cell"),  Input("pump_table", "active_cell"), Input("timestamp", "data"),
        Input("radio_trend", "value"),  Input("radio_pump", "value"),
        State("trend_table", "style_data_conditional"), State("pump_table", "style_data_conditional"),
        prevent_initial_call=True,
    )
    def select_altcoin(active_cell_trend, active_cell_pump, timestamp, filter_trend, filter_pump, style_trend, style_pump):
        logger.info(f"select_altcoin callback triggered with active_cell_trend: {active_cell_trend}, active_cell_pump: {active_cell_pump}, timestamp: {timestamp}, filter_trend: {filter_trend}, filter_pump: {filter_pump}")
        if ctx.triggered_id in ["timestamp", "radio_trend", "radio_pump"]:
            logger.debug("Removing highlighting due to data update or filter change")
            style_trend[1] = {}
            style_pump[1] = {}
            return no_update, None, [], style_trend, None, [], style_pump

        altcoin = no_update
        if ctx.triggered_id == "trend_table":
            if active_cell_trend:
                logger.debug(f"Highlighting trend table row: {active_cell_trend['row']}")
                condition = get_row_highlight_condition(active_cell_trend["row"])
                style_trend[1] = condition
                style_pump[1] = {}
                altcoin = active_cell_trend["row_id"]
            else:
                style_trend[1] = {}
                style_pump = no_update
        else:
            if active_cell_pump:
                logger.debug(f"Highlighting pump table row: {active_cell_pump['row']}")
                condition = get_row_highlight_condition(active_cell_pump["row"])
                style_pump[1] = condition
                style_trend[1] = {}
                altcoin = active_cell_pump["row_id"]
            else:
                style_pump[1] = {}
                style_trend = no_update
                
        logger.debug(f"Selected altcoin: {altcoin}")
        return altcoin, None, [], style_trend, None, [], style_pump

    @app.callback(
        Output("bar_chart", "children"),
        Input("timestamp", "data"),
        Input("radio_overview_filter", "value"),
        Input("radio_overview_timeframe", "value"),
        prevent_initial_call=True,
    )
    def update_overview_card(timestamp, filter, timeframe):
        logger.info(f"update_overview_card callback triggered with timestamp: {timestamp}, filter: {filter}, timeframe: {timeframe}")
        try:
            df = pd.read_csv(os.path.join("data", "market_data.csv"), index_col="name")
            col = f"gain_{timeframe.lower()}"
            btc_gain = df.loc["BTC", col]
            df = df.drop(["BTC"])
            df = filter_df(df, filter)
            df = df.sort_values(by=[col], ascending=False).iloc[:30]
            logger.debug(f"Filtered data for bar chart, shape: {df.shape}")
            return get_bar_figure(names=df.index, gains=df[col], btc_gain=btc_gain, timeframe=timeframe)
        except Exception as e:
            logger.error(f"Error in update_overview_card: {str(e)}")
            raise

    @app.callback(
        Output("bitcoin_chart", "children"),
        Input("timestamp", "data"),
        Input("radio_btc_chart", "value"),
        prevent_initial_call=True,
    )
    def update_bitcoin_chart(timestamp, timeframe):
        logger.info(f"update_bitcoin_chart callback triggered with timestamp: {timestamp}, timeframe: {timeframe}")
        try:
            klines = pd.read_csv(os.path.join("data", "klines", "BTC.csv"), index_col="timestamp")
            klines = add_emas(klines=klines, ema_lengths=[12, 21, 50])
            if timeframe == "1W":
                klines = klines.iloc[-42:]
            else:
                klines = klines.iloc[-186:]
            logger.debug(f"Prepared klines for Bitcoin chart, shape: {klines.shape}")
            return get_candlestick_figure(title="BTC / USD", klines=klines)
        except Exception as e:
            logger.error(f"Error in update_bitcoin_chart: {str(e)}")
            raise

    @app.callback(
        Output("altcoin_usd_chart", "children"), 
        Output("altcoin_btc_chart", "children"),
        Input("timestamp", "data"),
        Input("altcoin", "data"),
        Input("radio_altcoin_chart", "value"), 
        prevent_initial_call=True,
    )
    def update_altcoin_charts(timestamp, altcoin, timeframe):
        logger.info(f"update_altcoin_charts callback triggered with timestamp: {timestamp}, altcoin: {altcoin}, timeframe: {timeframe}")
        if altcoin in [None, ""]:
            logger.warning("No altcoin selected, preventing update")
            raise PreventUpdate
        
        try:
            btc_klines = pd.read_csv(os.path.join("data", "klines", "BTC.csv"), index_col="timestamp")
            usd_denom_klines = pd.read_csv(os.path.join("data", "klines", f"{altcoin}.csv"), index_col="timestamp")
            btc_denom_klines = pd.DataFrame(
                index=usd_denom_klines.index,
                data={
                    "open": usd_denom_klines["open"] / btc_klines["open"], 
                    "high": usd_denom_klines["high"] / btc_klines["close"],
                    "low": usd_denom_klines["low"] / btc_klines["close"], 
                    "close": usd_denom_klines["close"] / btc_klines["close"],
                },
            ).dropna()

            usd_denom_klines = add_emas(klines=usd_denom_klines, ema_lengths=[12, 21, 50])
            btc_denom_klines = add_emas(klines=btc_denom_klines, ema_lengths=[12, 21, 50])

            if timeframe == "1W":
                usd_denom_klines = usd_denom_klines.iloc[-42:]
                btc_denom_klines = btc_denom_klines.iloc[-42:]
            else:
                usd_denom_klines = usd_denom_klines.iloc[-186:]
                btc_denom_klines = btc_denom_klines.iloc[-186:]

            logger.debug(f"Prepared klines for altcoin charts, USD shape: {usd_denom_klines.shape}, BTC shape: {btc_denom_klines.shape}")
            usd_chart = get_candlestick_figure(title=f"{altcoin} / USD", klines=usd_denom_klines)
            btc_chart = get_candlestick_figure(title=f"{altcoin} / BTC", klines=btc_denom_klines)

            return usd_chart, btc_chart
        except Exception as e:
            logger.error(f"Error in update_altcoin_charts: {str(e)}")
            raise

    @app.callback(
        Output("bitcoin_tradingview", "children"),
        Output("bitcoin_exchanges", "children"),
        Input("timestamp", "data"),
        prevent_initial_call=True,
    )
    def update_bitcoin_links(timestamp):
        logger.info(f"update_bitcoin_links callback triggered with timestamp: {timestamp}")
        try:
            df = pd.read_csv(os.path.join("data", "config.csv"), index_col="name")
            tradingview_link = dbc.CardLink("TradingView", target="_blank", href=df.loc["BTC", "chart_usd"])
            
            exchange_links = []
            if type(df.loc["BTC", "spot_usd"]) == str:
                exchange_links.append(dbc.CardLink("Spot (USD)", target="_blank", href=df.loc["BTC", "spot_usd"]))
            if type(df.loc["BTC", "perps"]) == str:
                exchange_links.append(dbc.CardLink("Perpetuals", target="_blank", href=df.loc["BTC", "perps"]))

            logger.debug(f"Generated Bitcoin links: TradingView and {len(exchange_links)} exchange links")
            return tradingview_link, exchange_links
        except Exception as e:
            logger.error(f"Error in update_bitcoin_links: {str(e)}")
            raise

    @app.callback(
        Output("altcoin_tradingview", "children"),
        Output("altcoin_exchanges", "children"),
        Input("altcoin", "data"),
        prevent_initial_call=True,
    )
    
    def update_altcoin_links(altcoin):
        logger.info(f"update_altcoin_links callback triggered with altcoin: {altcoin}")
        try:
            df = pd.read_csv(os.path.join("data", "config.csv"), index_col="name")

            tradingview_links = []
            if type(df.loc[altcoin, "chart_usd"]) == str:
                tradingview_links.append(dbc.CardLink("TradingView (USD)", target="_blank", href=df.loc[altcoin, "chart_usd"]))
            if type(df.loc[altcoin, "chart_btc"]) == str:
                tradingview_links.append(dbc.CardLink("TradingView (BTC)", target="_blank", href=df.loc[altcoin, "chart_btc"]))

            exchange_links = []
            if type(df.loc[altcoin, "spot_usd"]) == str:
                exchange_links.append(dbc.CardLink("Spot (USD)", target="_blank", href=df.loc[altcoin, "spot_usd"]))
            if type(df.loc[altcoin, "spot_btc"]) == str:
                exchange_links.append(dbc.CardLink("Spot (BTC)", target="_blank", href=df.loc[altcoin, "spot_btc"]))
            if type(df.loc[altcoin, "perps"]) == str:
                exchange_links.append(dbc.CardLink("Perpetuals", target="_blank", href=df.loc[altcoin, "perps"]))

            logger.debug(f"Generated altcoin links: {len(tradingview_links)} TradingView and {len(exchange_links)} exchange links")
            return tradingview_links, exchange_links
        except Exception as e:
            logger.error(f"Error in update_altcoin_links: {str(e)}")
            raise

    logger.info("All callbacks registered successfully")