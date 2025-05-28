import sys
from pathlib import Path
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QSpinBox, QListWidget, QListWidgetItem, QFormLayout,
    QProgressBar, QGroupBox, QComboBox
)
from typing import List, Dict
from PyQt5.QtCore import Qt
from src.core.warehouse import DataWarehouse

class ClassPanel(QWidget):
    """Panel for training and evaluating KNN classifier on mushroom data."""
    def __init__(self, warehouse: DataWarehouse, parent=None):
        super().__init__(parent)
        self.warehouse = warehouse
        self.current_table = None
        self.init_ui()

    def init_ui(self):
        main = QVBoxLayout(self)

        # Feature selection
        feature_group = QGroupBox("Features")
        feature_layout = QVBoxLayout()
        
        self.feature_list = QListWidget()
        self.feature_list.setSelectionMode(QListWidget.MultiSelection)
        feature_layout.addWidget(QLabel("Select features for classification:"))
        feature_layout.addWidget(self.feature_list)
        
        feature_group.setLayout(feature_layout)
        main.addWidget(feature_group)

        # Model parameters
        param_group = QGroupBox("Model Parameters")
        param_layout = QFormLayout()
        
        self.k_spin = QSpinBox()
        self.k_spin.setRange(1, 10)
        self.k_spin.setValue(3)
        param_layout.addRow("Number of neighbors (k):", self.k_spin)
        
        self.train_size_spin = QSpinBox()
        self.train_size_spin.setRange(10, 90)
        self.train_size_spin.setValue(80)
        param_layout.addRow("Training set %:", self.train_size_spin)
        
        param_group.setLayout(param_layout)
        main.addWidget(param_group)

        # Training controls
        train_layout = QHBoxLayout()
        self.train_btn = QPushButton("Train Model")
        self.train_btn.setEnabled(False)
        train_layout.addWidget(self.train_btn)
        
        # Add save/load buttons
        self.save_model_btn = QPushButton("Save Model")
        self.save_model_btn.setEnabled(False)
        train_layout.addWidget(self.save_model_btn)
        
        self.load_model_btn = QPushButton("Load Model")
        train_layout.addWidget(self.load_model_btn)
        
        self.progress = QProgressBar()
        self.progress.setVisible(False)
        train_layout.addWidget(self.progress)
        main.addLayout(train_layout)

        # Results display
        results_group = QGroupBox("Results")
        self.results_form = QFormLayout()
        results_group.setLayout(self.results_form)
        main.addWidget(results_group)

        # Prediction section (initially hidden)
        self.predict_group = QGroupBox("Predict Single Mushroom")
        self.predict_group.setVisible(False)
        predict_layout = QFormLayout()
        
        # Will be populated with ComboBoxes for each feature when model is trained
        self.feature_inputs = {}  
        
        # Prediction button and result
        self.predict_btn = QPushButton("Predict")
        self.predict_result = QLabel()
        self.predict_result.setStyleSheet("font-weight: bold;")
        
        predict_layout.addRow(self.predict_btn)
        predict_layout.addRow("Prediction:", self.predict_result)
        
        self.predict_group.setLayout(predict_layout)
        main.addWidget(self.predict_group)

    def set_table(self, table_name: str):
        """Update controls when a new table is selected."""
        self.current_table = table_name
        self.feature_list.clear()
        self.results_form.removeRow(0)
        self.train_btn.setEnabled(False)
        self.save_model_btn.setEnabled(False)  # Add this line
        
        if table_name:
            table = self.warehouse.get_table(table_name)
            # Add all columns except 'class' as potential features
            for col in table.df.columns:
                if col != 'class':
                    self.feature_list.addItem(QListWidgetItem(col))
            self.train_btn.setEnabled(True)
        self.predict_group.setVisible(False)
        self.predict_result.clear()

    def setup_prediction_inputs(self, features: List[str]):
        """Setup input controls for prediction after model training."""
        # Clear existing inputs
        for cb in self.feature_inputs.values():
            cb.deleteLater()
        self.feature_inputs.clear()
        
        # Get prediction layout
        layout = self.predict_group.layout()
        
        # Remove all rows except the last two (predict button and result)
        while layout.rowCount() > 2:
            layout.removeRow(0)
            
        # Create ComboBox for each feature
        for feature in features:
            combo = QComboBox()
            coldef = self.warehouse.schema.column_defs[feature]
            # Add human-readable labels
            for code in sorted(coldef.codes):
                label = coldef.labels[code]
                combo.addItem(label, userData=code)  # Store code as item data
            self.feature_inputs[feature] = combo
            # Insert new rows at the beginning, before the button
            layout.insertRow(layout.rowCount()-2, f"{feature}:", combo)
    
        # Show the prediction section
        self.predict_group.setVisible(True)

    def get_prediction_input(self) -> Dict[str, str]:
        """Get the current feature values from input controls."""
        return {
            feature: combo.currentData()  # Get code from userData
            for feature, combo in self.feature_inputs.items()
        }