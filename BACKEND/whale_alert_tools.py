import os
from requests import Session, ConnectionError, Timeout, TooManyRedirects
from langchain.tools import tool
import time

# Load API key from environment variable
API_KEY = os.getenv('WHALE_ALERT_API_KEY')
if not API_KEY:
    raise ValueError("Please set the 'WHALE_ALERT_API_KEY' environment variable.")
if API_KEY.strip() == "":
    raise ValueError("The 'WHALE_ALERT_API_KEY' environment variable is empty.")

class WhaleAlertAPI:
    def __init__(self):
        self.api_key = API_KEY
        self.base_url = 'https://api.whale-alert.io/v1'
        self.headers = {
            'Accepts': 'application/json',
        }
        self.session = Session()
        self.session.headers.update(self.headers)

    def make_request(self, endpoint, parameters):
        try:
            parameters['api_key'] = self.api_key
            url = f"{self.base_url}/{endpoint}"
            response = self.session.get(url, params=parameters)
            
            if response.status_code != 200:
                print(f"Error: API returned status code {response.status_code}")
                print(f"Response content: {response.text}")
                return None
            
            data = response.json()
            return data
        except (ConnectionError, Timeout, TooManyRedirects) as e:
            print(f"Error fetching data from Whale Alert: {e}")
            return None
        except ValueError as e:
            print(f"Error parsing JSON response: {e}")
            print(f"Response content: {response.text}")
            return None

whale_alert_api = WhaleAlertAPI()

@tool
def get_whale_alert_status():
    """
    Get the current status of Whale Alert.
    """
    endpoint = 'status'
    parameters = {}
    return whale_alert_api.make_request(endpoint, parameters)



@tool
def get_recent_large_transactions(min_value=10000000, limit=5, currency=None):
    """
    Get recent large transactions from the last hour.
    Args:
    - min_value (int): Minimum USD value of transactions returned.
    - limit (int): Maximum number of results returned.
    - currency (str): Returns transactions for a specific currency code.
    """
    endpoint = 'transactions'
    current_time = int(time.time())
    one_hour_ago = current_time - 3600  # 3600 seconds = 1 hour
    parameters = {
        'start': one_hour_ago,
        'end': current_time,
        'min_value': min_value,
        'limit': limit
    }
    if currency:
        parameters['currency'] = currency
    return whale_alert_api.make_request(endpoint, parameters)
