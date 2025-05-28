import numpy as np
import pytest
from src.classification.base_classifier import Classifier
from src.classification.knn_classifier import KNNClassifier

class DummyClassifier(Classifier):
    def __init__(self):
        self.fitted = False

    def fit(self, X: np.ndarray, y: np.ndarray) -> 'DummyClassifier':
        self.fitted = True
        return self

    def predict(self, X: np.ndarray) -> np.ndarray:
        if not self.fitted:
            raise ValueError("DummyClassifier not fitted.")
        return np.zeros(len(X), dtype=int)


def test_dummy_classifier_predict_before_fit():
    dummy = DummyClassifier()
    with pytest.raises(ValueError):
        dummy.predict(np.array([[1], [2]]))


def test_dummy_classifier_score():
    dummy = DummyClassifier()
    X = np.array([[0], [1], [2]])
    y = np.array([0, 0, 0])
    dummy.fit(X, y)
    assert dummy.score(X, y) == 1.0


def test_knn_classifier_end_to_end():
    # Simple dataset: two clusters
    X = np.array([[0], [1], [10], [11]])
    y = np.array([0, 0, 1, 1])
    knn = KNNClassifier(n_neighbors=1)
    knn.fit(X, y)
    preds = knn.predict(X)
    assert np.array_equal(preds, y)
    assert knn.score(X, y) == 1.0


def test_knn_predict_before_fit():
    knn = KNNClassifier()
    with pytest.raises(ValueError):
        knn.predict(np.array([[0]]))