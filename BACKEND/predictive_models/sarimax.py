from statsmodels.tsa.statespace.sarimax import SARIMAX, SARIMAXResults
from sklearn.preprocessing import MinMaxScaler
import numpy as np

# Example evaluate_sarimax function implementation
def evaluate_sarimax(data, steps=5, exog=None):
    """Evaluate SARIMAX model predictions for a dataset."""
    if exog is None:
        exog = np.random.random((len(data), 1))  # Example external factors (replace this with your actual exogenous data)

    # Fit the SARIMAX model
    model = SARIMAX(data, exog=exog, order=(5, 1, 0), seasonal_order=(0, 0, 0, 0))
    model_fit = model.fit()

    # Ensure model_fit is of type SARIMAXResults
    if not isinstance(model_fit, SARIMAXResults):
        raise TypeError("Expected model_fit to be of type SARIMAXResults")

    # Make predictions
    predictions = model_fit.get_forecast(steps=steps, exog=exog[-steps:]).predicted_mean
    return predictions

class Sarimax:
    sc_in = MinMaxScaler(feature_range=(0, 1))
    sc_out = MinMaxScaler(feature_range=(0, 1))

    def __init__(self, args):
        self.train_size = -1
        self.test_size = -1
        self.order = tuple(map(int, args.order.split(', ')))
        self.seasonal_order = tuple(map(int, args.seasonal_order.split(', ')))
        self.enforce_invertibility = args.enforce_invertibility
        self.enforce_stationarity = args.enforce_stationarity

    def fit(self, data_x):
        data_x = np.array(data_x)
        train_x = data_x[:, 1:-1]
        train_y = data_x[:, -1]
        self.train_size = train_x.shape[0]
        train_x = self.sc_in.fit_transform(train_x)
        train_y = train_y.reshape(-1, 1)
        train_y = self.sc_out.fit_transform(train_y)
        train_x = np.array(train_x, dtype=float)
        train_y = np.array(train_y, dtype=float)
        self.model = SARIMAX(
            train_y,
            exog=train_x,
            order=self.order,
            seasonal_order=self.seasonal_order,
            enforce_invertibility=self.enforce_invertibility,
            enforce_stationarity=self.enforce_stationarity
        )
        result = self.model.fit()

        # Ensure result is of type SARIMAXResults
        if not isinstance(result, SARIMAXResults):
            raise TypeError("Expected result to be of type SARIMAXResults")

        self.result: SARIMAXResults = result

    def predict(self, test_x):
        test_x = np.array(test_x.iloc[:, 1:], dtype=float)
        test_x = self.sc_in.transform(test_x)
        self.test_size = test_x.shape[0]
        forecast_result = self.result.get_forecast(steps=self.test_size, exog=test_x)
        pred_y = forecast_result.predicted_mean
        pred_y = pred_y.reshape(-1, 1)
        pred_y = self.sc_out.inverse_transform(pred_y)
        return pred_y