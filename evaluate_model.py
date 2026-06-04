import os
import sys
import pickle
import numpy as np

# Try to import joblib and keras, but allow fallback if they aren't installed
try:
    import joblib
except ImportError:
    joblib = None

try:
    os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'  # Suppress TensorFlow logging
    from tensorflow import keras
except ImportError:
    keras = None

from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    matthews_corrcoef,
    confusion_matrix,
    classification_report
)

def load_model(model_path):
    """
    Loads a saved model based on the file extension.
    Supports Keras (.keras, .h5) and Pickle/Joblib (.pkl, .joblib) formats.
    """
    ext = os.path.splitext(model_path)[1].lower()
    
    if ext in ['.keras', '.h5']:
        if keras is None:
            raise ImportError("TensorFlow/Keras is required to load a Keras model but is not installed.")
        print(f"[INFO] Loading Keras model from {model_path}...")
        return keras.models.load_model(model_path)
    
    elif ext in ['.pkl', '.pickle']:
        print(f"[INFO] Loading Pickle model from {model_path}...")
        with open(model_path, 'rb') as f:
            return pickle.load(f)
            
    elif ext in ['.joblib']:
        if joblib is None:
            raise ImportError("Joblib is required to load a .joblib model but is not installed.")
        print(f"[INFO] Loading Joblib model from {model_path}...")
        return joblib.load(model_path)
        
    else:
        # Fallback attempts
        print(f"[WARNING] Unknown model format '{ext}'. Attempting to load using pickle...")
        try:
            with open(model_path, 'rb') as f:
                return pickle.load(f)
        except Exception:
            if joblib:
                try:
                    return joblib.load(model_path)
                except Exception:
                    pass
            raise ValueError(f"Could not load model at {model_path}. Unsupported or corrupt format.")

def evaluate_classification_model(model_path, X_test, y_test, report_path='evaluation_report.txt'):
    """
    Loads model, performs inference, calculates classification metrics,
    prints a clean report, and saves it to a file.
    """
    # 1. Load the model
    model = load_model(model_path)
    
    # 2. Perform inference
    # Check if this is a Keras model (which outputs probabilities for binary classification)
    if hasattr(model, 'predict_classes'):
        y_pred = model.predict_classes(X_test)
    else:
        # Standard predict call
        preds = model.predict(X_test)
        
        # If output contains class probabilities (e.g. Keras predict output shape is (N, 1) or (N, 2))
        if len(preds.shape) > 1 and preds.shape[1] > 1:
            y_pred = np.argmax(preds, axis=1)
        elif len(preds.shape) > 1 and preds.shape[1] == 1:
            # Binary probability output
            y_pred = (preds > 0.5).astype(int).flatten()
        else:
            # Discrete labels or single output list
            y_pred = preds
            
    # For binary metrics we assume 1D arrays
    y_test = np.array(y_test).flatten()
    y_pred = np.array(y_pred).flatten()
    
    # Ensure discrete binary class labels (0 or 1) for metrics
    if y_pred.dtype.kind in 'fc':  # float array
        y_pred = (y_pred > 0.5).astype(int)
        
    # 3. Calculate metrics
    accuracy = accuracy_score(y_test, y_pred)
    precision = precision_score(y_test, y_pred, zero_division=0)
    recall = recall_score(y_test, y_pred, zero_division=0)
    f1 = f1_score(y_test, y_pred, zero_division=0)
    mcc = matthews_corrcoef(y_test, y_pred)
    
    cm = confusion_matrix(y_test, y_pred)
    class_report = classification_report(y_test, y_pred, zero_division=0)
    
    # 4. Generate clean text report
    report_lines = [
        "============================================================",
        "             CLASSIFICATION MODEL EVALUATION REPORT          ",
        "============================================================",
        f"Model Evaluated : {os.path.basename(model_path)}",
        f"Evaluation Date : {np.datetime64('now')}",
        f"Test Samples    : {len(y_test)}",
        "------------------------------------------------------------",
        "METRICS SUMMARY:",
        f"  - Accuracy                     : {accuracy:.4f} ({accuracy * 100:.2f}%)",
        f"  - Precision (Class 1)          : {precision:.4f} ({precision * 100:.2f}%)",
        f"  - Recall (Class 1)             : {recall:.4f} ({recall * 100:.2f}%)",
        f"  - F1-Score                     : {f1:.4f} ({f1 * 100:.2f}%)",
        f"  - Matthews Correlation (MCC)   : {mcc:.4f}",
        "------------------------------------------------------------",
        "CONFUSION MATRIX:",
        f"  True Negative (TN)  : {cm[0][0]:<6} | False Positive (FP) : {cm[0][1]}",
        f"  False Negative (FN) : {cm[1][0]:<6} | True Positive (TP)  : {cm[1][1]}",
        "------------------------------------------------------------",
        "CLASSIFICATION REPORT DETAIL:",
        class_report,
        "============================================================"
    ]
    
    report_text = "\n".join(report_lines)
    
    # Print to console
    print(report_text)
    
    # Write to report file
    try:
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report_text)
        print(f"\n[SUCCESS] Evaluation report saved to: {os.path.abspath(report_path)}")
    except Exception as e:
        print(f"\n[ERROR] Failed to save evaluation report to {report_path}: {e}")

if __name__ == "__main__":
    # Example usage for manual execution/demo
    print("Evaluating with dummy data as demonstration...")
    
    # Create dummy data
    X_dummy = np.random.randn(100, 5)
    y_dummy = np.random.randint(0, 2, size=100)
    
    # Save a dummy random forest model for testing
    from sklearn.ensemble import RandomForestClassifier
    dummy_model = RandomForestClassifier(random_state=42)
    dummy_model.fit(X_dummy, y_dummy)
    
    test_model_path = "dummy_model.pkl"
    with open(test_model_path, "wb") as f:
        pickle.dump(dummy_model, f)
        
    # Evaluate dummy model
    evaluate_classification_model(test_model_path, X_dummy, y_dummy)
    
    # Clean up dummy model file
    if os.path.exists(test_model_path):
        os.remove(test_model_path)
