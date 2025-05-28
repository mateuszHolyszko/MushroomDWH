import numpy as np
from sklearn.neighbors import KNeighborsClassifier as SKKNN
from src.classification.base_classifier import Classifier

class KNNClassifier(Classifier):
    """
    K-Nearest Neighbors classifier wrapper around scikit-learn's implementation.
    """
    def __init__(self, n_neighbors: int = 3):
        self.n_neighbors = n_neighbors
        self._model = None

    def fit(self, X: np.ndarray, y: np.ndarray) -> 'KNNClassifier':
        """Fit KNN model. X should be shape (n_samples, n_features)."""
        self._model = SKKNN(n_neighbors=self.n_neighbors)
        self._model.fit(X, y)
        return self

    def predict(self, X: np.ndarray) -> np.ndarray:
        """Predict using the fitted KNN model."""
        if self._model is None:
            raise ValueError("KNNClassifier instance is not fitted yet.")
        return self._model.predict(X)