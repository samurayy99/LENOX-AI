from sklearn.ensemble import RandomForestRegressor
import numpy as np

# Example evaluate_randomforest function implementation
def evaluate_random_forest(data, target, test_size=0.2, n_estimators=100, random_state=42):
    """Evaluate Random Forest model predictions for a dataset."""
    # Split the dataset into training and test sets
    split_index = int((1 - test_size) * len(target))
    train_features, test_features = data[:split_index], data[split_index:]
    train_target, test_target = target[:split_index], target[split_index:]

    # Fit the Random Forest model
    model = RandomForestRegressor(n_estimators=n_estimators, random_state=random_state)
    model.fit(train_features, train_target)

    # Make predictions
    predictions = model.predict(test_features)

    return predictions, test_target

class RandomForest:
    def __init__(self, args):
        """
        Initialize the RandomForest model with the given arguments.
        
        Args:
            args: An object containing the arguments n_estimators and random_state.
        """
        self.n_estimators = args.n_estimators
        self.random_state = args.random_state
        self.model = RandomForestRegressor(n_estimators=self.n_estimators, random_state=self.random_state)

    def fit(self, data_x):
        """
        Fit the RandomForest model to the training data.
        
        Args:
            data_x: A 2D numpy array where the last column is the target variable.
        """
        data_x = np.array(data_x)
        train_x = data_x[:, 1:-1]
        train_y = data_x[:, -1]
        self.model.fit(train_x, train_y)

    def predict(self, test_x):
        """
        Predict using the fitted RandomForest model.
        
        Args:
            test_x: A DataFrame or 2D array containing the features for prediction.
        
        Returns:
            pred_y: The predicted values.
        """
        test_x = np.array(test_x.iloc[:, 1:], dtype=float)
        pred_y = self.model.predict(test_x)
        return pred_y
