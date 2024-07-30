import os
import nasdaqdatalink
from dotenv import load_dotenv
import os
import nasdaqdatalink
from dotenv import load_dotenv
from langchain.tools import tool
from typing import Optional, List, Dict, Union
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Configure Nasdaq Data Link
nasdaqdatalink.ApiConfig.api_key = os.getenv('NASDAQ_DATA_LINK_API_KEY')
nasdaqdatalink.ApiConfig.use_retries = True

@tool
def get_nasdaq_data(dataset_code: str, start_date: Optional[str] = None, end_date: Optional[str] = None, 
                    collapse: Optional[str] = None, transformation: Optional[str] = None, 
                    column_index: Optional[Union[int, List[int]]] = None, 
                    order: Optional[str] = None, rows: Optional[int] = None) -> Dict:
    """
    Fetches data from Nasdaq Data Link API.

    Args:
    dataset_code (str): The Nasdaq Data Link code for the dataset (e.g., 'WIKI/AAPL' for Apple stock data)
    start_date (str, optional): Start date for the data in YYYY-MM-DD format
    end_date (str, optional): End date for the data in YYYY-MM-DD format
    collapse (str, optional): Sampling frequency (e.g., 'annual', 'quarterly', 'monthly', 'weekly', 'daily')
    transformation (str, optional): Data transformation (e.g., 'diff', 'rdiff', 'cumul', 'normalize')
    column_index (int or List[int], optional): Column index or list of column indices to return
    order (str, optional): Sort order, either 'asc' or 'desc'
    rows (int, optional): Number of rows to return

    Returns:
    Dict: A dictionary containing the requested data and metadata
    """
    try:
        data = nasdaqdatalink.get(dataset_code, 
                                  start_date=start_date, 
                                  end_date=end_date,
                                  collapse=collapse,
                                  transformation=transformation,
                                  column_index=column_index,
                                  order=order,
                                  rows=rows)
        
        return {
            "data": data.to_dict(orient='records'),
            "columns": list(data.columns),
            "index": list(data.index),
        }
    except Exception as e:
        logger.error(f"Error occurred while fetching data: {str(e)}")
        return {"error": str(e)}

@tool
def get_nasdaq_table(datatable_code: str, **kwargs) -> Dict:
    """
    Fetches data from Nasdaq Data Link Datatables API.

    Args:
    datatable_code (str): The Nasdaq Data Link code for the datatable
    **kwargs: Additional parameters to filter the data

    Returns:
    Dict: A dictionary containing the requested data and metadata
    """
    try:
        data = nasdaqdatalink.get_table(datatable_code, **kwargs)
        return {
            "data": data.to_dict(orient='records'),
            "columns": list(data.columns),
        }
    except Exception as e:
        logger.error(f"Error occurred while fetching datatable: {str(e)}")
        return {"error": str(e)}

@tool
def get_bitcoin_insights(metrics: Optional[List[str]] = None, start_date: Optional[str] = None, end_date: Optional[str] = None) -> Dict:
    """
    Fetches Bitcoin Data Insights from Nasdaq Data Link.

    Args:
    metrics (List[str], optional): List of Bitcoin metric codes to fetch. If None, fetches all metrics.
    start_date (str, optional): Start date for the data in YYYY-MM-DD format.
    end_date (str, optional): End date for the data in YYYY-MM-DD format.

    Returns:
    Dict: A dictionary containing the requested Bitcoin metrics.
    """
    return get_nasdaq_data("BCHAIN/MKPRU", start_date=start_date, end_date=end_date, column_index=metrics)

# Bitcoin metric codes dictionary for reference
BITCOIN_METRICS = {
    "TOTBC": "Total Bitcoins",
    "MKPRU": "Bitcoin Market Price USD",
    "ATRCT": "Bitcoin Median Transaction Conf. Time",
    "AVBLS": "Bitcoin Average Block Size",
    "BLCHS": "Bitcoin api.blockchain Size",
    "CPTRA": "Bitcoin Cost Per Transaction",
    "CPTRV": "Bitcoin Cost % of Transaction Volume",
    "DIFF": "Bitcoin Difficulty",
    "ETRAV": "Bitcoin Estimated Transaction Volume",
    "ETRVU": "Bitcoin Estimated Transaction Vol. USD",
    "HRATE": "Bitcoin Hash Rate",
    "MIREV": "Bitcoin Miners Revenue",
    "MKTCP": "Bitcoin Market Capitalization",
    "MWNTD": "Bitcoin My Wallet Number of Tx Per Day",
    "MWNUS": "Bitcoin My Wallet Number of Users",
    "MWTRV": "Bitcoin My Wallet Transaction Volume",
    "NADDU": "Bitcoin Number of Unique Addr. Used",
    "NTRAN": "Bitcoin Number of Transactions",
    "NTRAT": "Bitcoin Total Number of Transactions",
    "NTRBL": "Bitcoin Number of Tx per Block",
    "NTREP": "Bitcoin Tx Excluding Popular Addresses",
    "TOUTV": "Bitcoin Total Output Volume",
    "TRFEE": "Bitcoin Total Transaction Fees",
    "TRFUS": "Bitcoin Total Transaction Fees USD",
    "TRVOU": "Bitcoin USD Exchange Trade Volume",
}