from sklearn.ensemble import RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import r2_score
import pandas as pd
import numpy as np

def preprocess_data(data):
    """Preprocess the input data, including handling missing values and scaling features."""
    # Convert datetime features to numerical format
    for col in data.select_dtypes(include=['datetime', 'datetime64']).columns:
        data[col] = data[col].map(pd.Timestamp.toordinal)
    
    # Drop the Date column if it exists
    if 'Date' in data.columns:
        data = data.drop(columns=['Date'])
    
    # Impute missing values
    imputer = SimpleImputer(missing_values=np.nan, strategy="mean")
    data = pd.DataFrame(imputer.fit_transform(data), columns=data.columns)
    
    return data

def evaluate_random_forest(data, target, test_size=0.2, n_estimators=100, random_state=42):
    """Evaluate Random Forest model predictions for a dataset."""
    data = preprocess_data(data)
    
    # Split the dataset into training and test sets
    train_features, test_features, train_target, test_target = train_test_split(data, target, test_size=test_size, random_state=random_state)

    # Scale the features
    scaler = StandardScaler()
    train_features = scaler.fit_transform(train_features)
    test_features = scaler.transform(test_features)

    # Fit the Random Forest model
    model = RandomForestRegressor(n_estimators=n_estimators, random_state=random_state)
    model.fit(train_features, train_target)

    # Make predictions
    predictions = model.predict(test_features)
    # Calculate r2 score
    score = r2_score(test_target, predictions)
    return predictions, score

class RandomForest:
    def __init__(self, args):
        self.n_estimators = args.n_estimators
        self.random_state = args.random_state
        self.model = RandomForestRegressor(n_estimators=self.n_estimators, random_state=self.random_state)

    def fit(self, data_x, data_y):
        data_x = preprocess_data(data_x)
        
        # Scale the features
        scaler = StandardScaler()
        data_x = scaler.fit_transform(data_x)
        
        self.model.fit(data_x, data_y)

    def predict(self, data_x):
        data_x = preprocess_data(data_x)
        
        # Scale the features
        scaler = StandardScaler()
        data_x = scaler.transform(data_x)
        
        return self.model.predict(data_x)
