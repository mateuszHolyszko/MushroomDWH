from abc import ABC, abstractmethod
import numpy as np

class Classifier(ABC):
    """
    Abstract base classifier interface.
    """
    @abstractmethod
    def fit(self, X: np.ndarray, y: np.ndarray) -> 'Classifier':
        """Fit the model to training data."""
        pass

    @abstractmethod
    def predict(self, X: np.ndarray) -> np.ndarray:
        """Predict labels for input data."""
        pass

    def score(self, X: np.ndarray, y: np.ndarray) -> float:
        """
        Compute accuracy of predictions on X against true labels y.
        """
        preds = self.predict(X)
        if len(preds) != len(y):
            raise ValueError("Prediction and true label arrays must have the same length.")
        return float((preds == y).mean())