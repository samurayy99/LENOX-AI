from statsmodels.tsa.arima.model import ARIMA
from sklearn.preprocessing import MinMaxScaler
import numpy as np
from statsmodels.tsa.stattools import adfuller
import pandas as pd

def make_stationary(data):
    """Make the time series data stationary."""
    result = adfuller(data)
    if result[1] > 0.05:  # p-value > 0.05 indicates non-stationarity
        return data.diff().dropna()  # Differencing
    return data


def evaluate_arima(data, steps=30):
    """Evaluate ARIMA model predictions for a dataset."""
    data = make_stationary(data)
    model = ARIMA(data, order=(5, 1, 2))  # Adjusted parameters
    model_fit = model.fit()
    predictions = model_fit.forecast(steps=steps)

    # Inverse transformation to get back to the original scale
    last_value = data.iloc[-1]
    predictions = predictions.cumsum() + last_value

    return predictions

class MyARIMA:
    sc_in = MinMaxScaler(feature_range=(0, 1))
    sc_out = MinMaxScaler(feature_range=(0, 1))

    def __init__(self, args):
        """
        Initialize the ARIMA model with the given arguments.
        
        Args:
            args: An object containing the order of the ARIMA model.
        """
        self.train_size = -1
        self.test_size = -1
        self.order = tuple(map(int, args.order.split(', ')))

    def fit(self, data_x):
        """
        Fit the ARIMA model to the training data.
        
        Args:
            data_x: A 2D numpy array where the last column is the target variable.
        """
        data_x = np.array(data_x)
        train_x = data_x[:, 1:-1]
        train_y = data_x[:, -1]
        self.train_size = train_x.shape[0]
        train_x = self.sc_in.fit_transform(train_x)
        train_y = train_y.reshape(-1, 1)
        train_y = self.sc_out.fit_transform(train_y)
        train_x = np.array(train_x, dtype=float)
        train_y = np.array(train_y, dtype=float)
        train_y = make_stationary(pd.Series(train_y.flatten()))
        self.model = ARIMA(train_y, exog=train_x, order=self.order)
        self.result = self.model.fit()

    def predict(self, test_x):
        """
        Predict using the fitted ARIMA model.
        
        Args:
            test_x: A DataFrame or 2D array containing the features for prediction.
        
        Returns:
            pred_y: The predicted values.
        """
        test_x = np.array(test_x.iloc[:, 1:], dtype=float)
        test_x = self.sc_in.transform(test_x)
        self.test_size = test_x.shape[0]
        pred_y = self.result.predict(start=self.train_size, end=self.train_size + self.test_size - 1, exog=test_x)
        pred_y = pred_y.reshape(-1, 1)
        pred_y = self.sc_out.inverse_transform(pred_y)
        return pred_y
