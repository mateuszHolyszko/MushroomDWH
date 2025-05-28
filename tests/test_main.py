import sys
from pathlib import Path

# Add project root to Python path
project_root = str(Path(__file__).parent.parent)
if project_root not in sys.path:
    sys.path.append(project_root)

from src.core.warehouse import DataWarehouse
from src.extractor.subset_extractor import SubsetExtractor
from src.preprocessing.encoder import LabelEncoder, OneHotEncoder
from src.classification.knn_classifier import KNNClassifier
import numpy as np


def print_separator():
    print("\n" + "="*80 + "\n")

def main():
    # Initialize warehouse and load data
    print("Initializing warehouse and loading mushroom data...")
    warehouse = DataWarehouse()
    warehouse.load_table('mushrooms', 'data/agaricus-lepiota.data')
    table = warehouse.get_table('mushrooms')
    print(f"Loaded {len(table)} mushroom records")
    
    print_separator()
    
    # Basic statistics
    print("Computing basic statistics for numeric-encoded class labels...")
    encoder = LabelEncoder('class', warehouse.schema)
    class_values = encoder.transform(table.df['class'])
    edible_count = sum(class_values == 0)
    poisonous_count = sum(class_values == 1)
    print(f"Dataset composition:")
    print(f"- Edible mushrooms: {edible_count} ({edible_count/len(table)*100:.1f}%)")
    print(f"- Poisonous mushrooms: {poisonous_count} ({poisonous_count/len(table)*100:.1f}%)")
    
    print_separator()
    
    # Data extraction examples
    print("Testing data extraction capabilities...")
    extractor = SubsetExtractor(warehouse)
    
    # Get first 5 rows
    head = extractor.extract_rows('mushrooms', end=5)
    print("\nFirst 5 records:")
    print(head.df)
    
    # Get mushrooms with specific characteristics
    almond_odor = extractor.extract_by_value('mushrooms', {'odor': 'a'})
    print(f"\nMushrooms with almond odor: {len(almond_odor)} records")
    
    white_cap_edible = extractor.extract_by_value('mushrooms', {
        'cap_color': 'w',
        'class': 'e'
    })
    print(f"White-capped edible mushrooms: {len(white_cap_edible)} records")
    
    print_separator()
    
    # Feature analysis
    print("Analyzing important features...")
    
    # Get odor distribution for edible vs poisonous
    table = warehouse.get_table('mushrooms')
    odor_class = table.df[['odor', 'class']].value_counts().unstack()
    print("\nOdor distribution by class:")
    print(odor_class)
    
    print_separator()
    
    # Classification example
    print("Running simple classification example...")
    
    # Prepare features
    features = ['odor', 'spore_print_color', 'gill_color']
    X_table = extractor.extract_columns('mushrooms', features)
    
    # Encode features
    encoded_features = []
    for feature in features:
        encoder = LabelEncoder(feature, warehouse.schema)
        encoded_features.append(encoder.transform(X_table.df[feature]))
    X = np.column_stack(encoded_features)
    
    # Encode target
    y_encoder = LabelEncoder('class', warehouse.schema)
    y = y_encoder.transform(table.df['class'])
    
    # Train KNN classifier
    knn = KNNClassifier(n_neighbors=3)
    # Use first 80% for training
    train_size = int(0.8 * len(X))
    X_train, y_train = X[:train_size], y[:train_size]
    X_test, y_test = X[train_size:], y[train_size:]
    
    knn.fit(X_train, y_train)
    accuracy = knn.score(X_test, y_test)
    print(f"\nKNN Classifier accuracy on test set: {accuracy*100:.1f}%")

if __name__ == "__main__":
    main()