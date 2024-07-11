import logging
import math
import numpy as np
import sklearn.metrics

logger = logging.getLogger(__name__)

def preprocess(pred, target, is_regression=False):
    """Preprocess predictions and targets for classification metrics."""
    if is_regression:
        y_test = []
        prediction = []
        for i in range(len(target) - 1):
            m1 = target[i + 1] - target[i]
            m2 = pred[i + 1] - pred[i]
            y_test.append(m1 > 0)
            prediction.append(m2 > 0)
        return y_test, prediction
    return target, pred

def accuracy_score(pred, target, is_regression=False):
    """Calculate accuracy score."""
    y_test, prediction = preprocess(pred, target, is_regression)
    return sklearn.metrics.accuracy_score(y_test, prediction)

def f1_score(pred, target, is_regression=False):
    """Calculate F1 score."""
    y_test, prediction = preprocess(pred, target, is_regression)
    return sklearn.metrics.f1_score(y_test, prediction)

def recall_score(pred, target, is_regression=False):
    """Calculate recall score."""
    y_test, prediction = preprocess(pred, target, is_regression)
    return sklearn.metrics.recall_score(y_test, prediction)

def precision_score(pred, target, is_regression=False):
    """Calculate precision score."""
    y_test, prediction = preprocess(pred, target, is_regression)
    return sklearn.metrics.precision_score(y_test, prediction)

def classification_report(pred, target, is_regression=False):
    """Generate classification report."""
    y_test, prediction = preprocess(pred, target, is_regression)
    return sklearn.metrics.classification_report(y_test, prediction)

def confusion_matrix(pred, target, is_regression=False):
    """Generate confusion matrix."""
    y_test, prediction = preprocess(pred, target, is_regression)
    return sklearn.metrics.confusion_matrix(y_test, prediction)

def rmse(pred, target):
    """Calculate Root Mean Square Error."""
    return math.sqrt(np.mean((np.array(pred) - np.array(target)) ** 2))

def mae(pred, target):
    """Calculate Mean Absolute Error."""
    return np.mean(np.abs(np.array(pred) - np.array(target)))

def mape(pred, target):
    """Calculate Mean Absolute Percentage Error."""
    return np.mean(np.abs((np.array(target) - np.array(pred)) / np.array(target))) * 100

def smape(pred, target):
    """Calculate Symmetric Mean Absolute Percentage Error."""
    return 100 * np.mean(np.abs(np.array(pred) - np.array(target)) / ((np.abs(np.array(pred)) + np.abs(np.array(target))) / 2))

def mase(pred, target, sp=365):
    """Calculate Mean Absolute Scaled Error."""
    y_pred_naive = target[:-sp]
    mae_naive = np.mean(np.abs(target[sp:] - y_pred_naive))
    if mae_naive == 0:
        return np.nan
    return np.mean(np.abs(target - pred)) / mae_naive

def msle(pred, target, squared=True):
    """Calculate Mean Squared Logarithmic Error."""
    if squared:
        return np.mean(np.power(np.log(np.array(pred).astype(float) + 1) - np.log(np.array(target).astype(float) + 1), 2))
    return np.sqrt(np.mean(np.power(np.log(np.array(pred).astype(float) + 1) - np.log(np.array(target).astype(float) + 1), 2)))
