import numpy as np
from PyQt5.QtWidgets import QMessageBox, QLabel, QFileDialog
from PyQt5.QtCore import QTimer
from src.classification.knn_classifier import KNNClassifier
from src.preprocessing.encoder import LabelEncoder
from src.gui.views.class_panel import ClassPanel
from src.core.table_store import TableStore
import pickle
from dataclasses import dataclass
from typing import Dict, List

@dataclass
class ModelState:
    """Class to store all necessary model information"""
    classifier: KNNClassifier
    feature_encoders: Dict[str, LabelEncoder]
    y_encoder: LabelEncoder
    selected_features: List[str]
    k_neighbors: int
    train_accuracy: float
    test_accuracy: float

class ClassController:
    """Controller for the classification panel."""
    def __init__(self, main_window):
        self.main = main_window
        self.panel: ClassPanel = main_window.class_panel
        self.table_store = main_window.table_store
        
        # Model state
        self.classifier = None
        self.feature_encoders = {}
        self.y_encoder = None 
        self.selected_features = None
        self.train_accuracy = None
        self.test_accuracy = None

        # Connect signals after all attributes are initialized
        self._connect_signals()

    def _connect_signals(self):
        """Connect all panel signals to their handlers."""
        self.panel.train_btn.clicked.connect(self.on_train)
        # Only connect save/load if they exist
        if hasattr(self.panel, 'save_model_btn'):
            self.panel.save_model_btn.clicked.connect(self.on_save_model)
        if hasattr(self.panel, 'load_model_btn'):
            self.panel.load_model_btn.clicked.connect(self.on_load_model)
        if hasattr(self.panel, 'predict_btn'):
            self.panel.predict_btn.clicked.connect(self.on_predict)

    def on_train(self):
        """Handle model training and evaluation."""
        if not self.table_store.active_table_name:
            QMessageBox.warning(self.main, "No Data", 
                              "Please load a dataset first.")
            return

        # Get selected features
        selected_items = self.panel.feature_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self.main, "No Features", 
                              "Please select at least one feature.")
            return
        
        features = [item.text() for item in selected_items]
        
        # Get data from active table
        table = self.table_store.get_active_table()
        
        # Prepare feature matrix X
        X_encoded = []
        self.feature_encoders = {}
        for feature in features:
            encoder = LabelEncoder(feature, self.table_store.schema)
            encoded_col = encoder.transform(table.df[feature])
            X_encoded.append(encoded_col)
            self.feature_encoders[feature] = encoder
        X = np.column_stack(X_encoded)
        
        # Prepare target y
        self.y_encoder = LabelEncoder('class', self.table_store.schema)
        y = self.y_encoder.transform(table.df['class'])
        
        # Split data
        train_percent = self.panel.train_size_spin.value()
        train_size = int(len(X) * train_percent / 100)
        indices = np.random.permutation(len(X))
        X_train = X[indices[:train_size]]
        X_test = X[indices[train_size:]]
        y_train = y[indices[:train_size]]
        y_test = y[indices[train_size:]]
        
        # Show progress bar
        self.panel.progress.setVisible(True)
        self.panel.progress.setValue(0)
        
        # Train model
        k = self.panel.k_spin.value()
        self.classifier = KNNClassifier(n_neighbors=k)
        self.classifier.fit(X_train, y_train)
        
        # Update progress
        self.panel.progress.setValue(50)
        
        # Store selected features
        self.selected_features = features
        
        # Evaluate
        train_acc = self.classifier.score(X_train, y_train)
        test_acc = self.classifier.score(X_test, y_test)
        
        # Display results
        while self.panel.results_form.rowCount() > 0:
            self.panel.results_form.removeRow(0)
            
        self.panel.results_form.addRow("Training Accuracy:", 
                                     QLabel(f"{train_acc*100:.1f}%"))
        self.panel.results_form.addRow("Test Accuracy:", 
                                     QLabel(f"{test_acc*100:.1f}%"))
        self.panel.results_form.addRow("Number of Training Samples:", 
                                     QLabel(str(len(X_train))))
        self.panel.results_form.addRow("Number of Test Samples:", 
                                     QLabel(str(len(X_test))))
        
        # Setup prediction inputs
        self.panel.setup_prediction_inputs(features)
        
        # Enable save model button
        self.panel.save_model_btn.setEnabled(True)
        
        # Complete progress
        self.panel.progress.setValue(100)
        QTimer.singleShot(1000, lambda: self.panel.progress.setVisible(False))
        
        # Update status
        self.main.status_bar.showMessage(
            f"Model trained with {len(features)} features. "
            f"Test accuracy: {test_acc*100:.1f}%"
        )

        # Store training results
        self.train_accuracy = train_acc
        self.test_accuracy = test_acc
        
        # Enable save button after successful training
        self.panel.save_model_btn.setEnabled(True)

        # Store selected features
        self.selected_features = features  # Add this line
        
        # Setup prediction inputs after successful training
        self.panel.setup_prediction_inputs(features)

    def on_predict(self):
        """Handle single mushroom prediction."""
        if not self.classifier or not self.selected_features:
            QMessageBox.warning(self.main, "No Model", 
                              "Please train a model first.")
            return
        
        # Get input values
        input_data = self.panel.get_prediction_input()
        
        # Encode features
        X_pred = []
        for feature in self.selected_features:
            encoded = self.feature_encoders[feature].transform([input_data[feature]])
            X_pred.append(encoded)
        X_pred = np.column_stack(X_pred)
        
        # Get prediction
        pred_idx = self.classifier.predict(X_pred)[0]
        pred_code = self.y_encoder.int_to_code[pred_idx]
        
        # Show result with label using schema from table_store
        pred_label = self.main.table_store.schema.column_defs['class'].labels[pred_code]
        self.panel.predict_result.setText(pred_label)
        
        # Color code the result
        color = "darkgreen" if pred_code == 'e' else "darkred"
        self.panel.predict_result.setStyleSheet(f"font-weight: bold; color: {color}")

    def on_save_model(self):
        """Save trained model and associated data to file."""
        if not self.classifier or not self.selected_features:
            QMessageBox.warning(self.main, "No Model", 
                              "Please train a model first.")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self.main,
            "Save Model",
            "",
            "Model Files (*.model);;All Files (*)"
        )
        
        if not file_path:
            return
            
        if not file_path.endswith('.model'):
            file_path += '.model'

        # Create state object with all necessary data
        state = ModelState(
            classifier=self.classifier,
            feature_encoders=self.feature_encoders,
            y_encoder=self.y_encoder,
            selected_features=self.selected_features,
            k_neighbors=self.panel.k_spin.value(),
            train_accuracy=self.train_accuracy,
            test_accuracy=self.test_accuracy
        )

        try:
            with open(file_path, 'wb') as f:
                pickle.dump(state, f)
            self.main.status_bar.showMessage(f"Model saved to {file_path}")
        except Exception as e:
            QMessageBox.critical(self.main, "Error Saving Model", str(e))

    def on_load_model(self):
        """Load model and associated data from file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self.main,
            "Load Model",
            "",
            "Model Files (*.model);;All Files (*)"
        )
        
        if not file_path:
            return

        try:
            with open(file_path, 'rb') as f:
                state: ModelState = pickle.load(f)

            # Restore model state
            self.classifier = state.classifier
            self.feature_encoders = state.feature_encoders
            self.y_encoder = state.y_encoder
            self.selected_features = state.selected_features
            self.train_accuracy = state.train_accuracy
            self.test_accuracy = state.test_accuracy

            # Update UI
            self.panel.k_spin.setValue(state.k_neighbors)
            
            # Update results display
            while self.panel.results_form.rowCount() > 0:
                self.panel.results_form.removeRow(0)
                
            self.panel.results_form.addRow(
                "Training Accuracy:", 
                QLabel(f"{state.train_accuracy*100:.1f}%")
            )
            self.panel.results_form.addRow(
                "Test Accuracy:", 
                QLabel(f"{state.test_accuracy*100:.1f}%")
            )

            # Setup prediction inputs
            self.panel.setup_prediction_inputs(state.selected_features)
            
            # Enable save button and prediction group
            self.panel.save_model_btn.setEnabled(True)
            self.panel.predict_group.setVisible(True)
            
            self.main.status_bar.showMessage(
                f"Model loaded from {file_path} with {len(state.selected_features)} features"
            )

        except Exception as e:
            QMessageBox.critical(self.main, "Error Loading Model", str(e))