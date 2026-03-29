"""
model.py
--------
Trains Random Forest (primary) and Isolation Forest (anomaly scoring)
on the NSL-KDD dataset. Evaluates and saves models + visualizations.
Run: python model.py
"""

import os
import joblib
import numpy as np
import matplotlib
matplotlib.use("Agg")          # Non-interactive backend for server use
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.ensemble import RandomForestClassifier, IsolationForest
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score,
    f1_score, confusion_matrix, classification_report,
)

from preprocess import load_and_preprocess

# -------------------------------------------------------------------
# Paths
# -------------------------------------------------------------------
BASE_DIR    = os.path.dirname(__file__)
MODELS_DIR  = os.path.join(BASE_DIR, "models")
STATIC_DIR  = os.path.join(BASE_DIR, "static")
RF_MODEL_PATH = os.path.join(MODELS_DIR, "rf_model.pkl")
IF_MODEL_PATH = os.path.join(MODELS_DIR, "if_model.pkl")

os.makedirs(MODELS_DIR, exist_ok=True)
os.makedirs(STATIC_DIR, exist_ok=True)


# -------------------------------------------------------------------
# Training
# -------------------------------------------------------------------
def train_random_forest(X_train, y_train, n_estimators: int = 100, random_state: int = 42):
    """Train and return a Random Forest classifier."""
    print("[MODEL] Training Random Forest ...")
    rf = RandomForestClassifier(
        n_estimators=n_estimators,
        max_depth=20,
        min_samples_split=5,
        class_weight="balanced",   # handles imbalanced classes
        random_state=random_state,
        n_jobs=-1,
    )
    rf.fit(X_train, y_train)
    print("[MODEL] Random Forest training complete.")
    return rf


def train_isolation_forest(X_train, contamination: float = 0.1, random_state: int = 42):
    """Train and return an Isolation Forest for unsupervised anomaly scoring."""
    print("[MODEL] Training Isolation Forest ...")
    iso = IsolationForest(
        n_estimators=100,
        contamination=contamination,
        random_state=random_state,
        n_jobs=-1,
    )
    iso.fit(X_train)
    print("[MODEL] Isolation Forest training complete.")
    return iso


# -------------------------------------------------------------------
# Evaluation
# -------------------------------------------------------------------
def evaluate(model, X_test, y_test):
    """Return a dict of evaluation metrics and predictions."""
    y_pred = model.predict(X_test)

    # RF returns 0/1; IF returns 1 (normal) / -1 (anomaly) → remap
    if hasattr(model, "predict_proba"):
        proba = model.predict_proba(X_test)[:, 1]
    else:
        # Isolation Forest: use decision_function (lower = more anomalous)
        y_pred = np.where(y_pred == -1, 1, 0)
        proba = -model.decision_function(X_test)   # higher = more anomalous
        proba = (proba - proba.min()) / (proba.max() - proba.min() + 1e-9)

    metrics = {
        "accuracy":  accuracy_score(y_test, y_pred),
        "precision": precision_score(y_test, y_pred, zero_division=0),
        "recall":    recall_score(y_test, y_pred, zero_division=0),
        "f1":        f1_score(y_test, y_pred, zero_division=0),
        "cm":        confusion_matrix(y_test, y_pred),
        "y_pred":    y_pred,
        "y_proba":   proba,
    }

    print("\n" + "=" * 50)
    print(f"  Accuracy : {metrics['accuracy']*100:.2f}%")
    print(f"  Precision: {metrics['precision']*100:.2f}%")
    print(f"  Recall   : {metrics['recall']*100:.2f}%")
    print(f"  F1-Score : {metrics['f1']*100:.2f}%")
    print("=" * 50)
    print(classification_report(y_test, y_pred, target_names=["Normal", "Attack"]))

    return metrics


# -------------------------------------------------------------------
# Visualization — computed ONCE, saved to static/
# -------------------------------------------------------------------
def save_confusion_matrix(cm: np.ndarray, path: str):
    """Save a styled confusion matrix heatmap."""
    fig, ax = plt.subplots(figsize=(6, 5))
    sns.heatmap(
        cm, annot=True, fmt="d", cmap="Blues",
        xticklabels=["Normal", "Attack"],
        yticklabels=["Normal", "Attack"],
        ax=ax,
    )
    ax.set_title("Confusion Matrix", fontsize=14, fontweight="bold")
    ax.set_xlabel("Predicted Label")
    ax.set_ylabel("True Label")
    plt.tight_layout()
    fig.savefig(path, dpi=120)
    plt.close(fig)
    print(f"[VIZ] Confusion matrix saved → {path}")


def save_metrics_chart(metrics: dict, path: str):
    """Save a bar chart of accuracy, precision, recall, F1."""
    labels  = ["Accuracy", "Precision", "Recall", "F1-Score"]
    values  = [
        metrics["accuracy"] * 100,
        metrics["precision"] * 100,
        metrics["recall"] * 100,
        metrics["f1"] * 100,
    ]
    colors = ["#4f8ef7", "#43c59e", "#f7a84f", "#f76f6f"]

    fig, ax = plt.subplots(figsize=(7, 4))
    bars = ax.bar(labels, values, color=colors, edgecolor="white", linewidth=0.8)
    ax.set_ylim(0, 110)
    ax.set_ylabel("Score (%)")
    ax.set_title("Model Performance Metrics", fontsize=14, fontweight="bold")
    for bar, val in zip(bars, values):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 1.5,
            f"{val:.1f}%", ha="center", va="bottom", fontsize=11, fontweight="bold",
        )
    plt.tight_layout()
    fig.savefig(path, dpi=120)
    plt.close(fig)
    print(f"[VIZ] Metrics chart saved → {path}")


def save_feature_importance(model, feature_names: list, path: str, top_n: int = 15):
    """Save top-N feature importance bar chart (RF only)."""
    if not hasattr(model, "feature_importances_"):
        return
    importances = model.feature_importances_
    indices = np.argsort(importances)[::-1][:top_n]
    top_features = [feature_names[i] for i in indices]
    top_values   = importances[indices]

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.barh(top_features[::-1], top_values[::-1], color="#4f8ef7")
    ax.set_xlabel("Importance")
    ax.set_title(f"Top {top_n} Feature Importances (Random Forest)", fontweight="bold")
    plt.tight_layout()
    fig.savefig(path, dpi=120)
    plt.close(fig)
    print(f"[VIZ] Feature importance saved → {path}")


# -------------------------------------------------------------------
# Main entry point
# -------------------------------------------------------------------
def main():
    # 1. Preprocess
    X_train, X_test, y_train, y_test, feature_names, scaler, encoders = load_and_preprocess()

    # 2. Train Random Forest
    rf_model = train_random_forest(X_train, y_train)

    # 3. Evaluate
    print("\n--- Random Forest Evaluation ---")
    metrics = evaluate(rf_model, X_test, y_test)

    # 4. Save models
    joblib.dump(rf_model, RF_MODEL_PATH)
    joblib.dump(scaler,   os.path.join(MODELS_DIR, "scaler.pkl"))
    joblib.dump(encoders, os.path.join(MODELS_DIR, "encoders.pkl"))
    print(f"[MODEL] Saved RF model  → {RF_MODEL_PATH}")

    # 5. Optional: Isolation Forest
    iso_model = train_isolation_forest(X_train)
    joblib.dump(iso_model, IF_MODEL_PATH)
    print(f"[MODEL] Saved IF model  → {IF_MODEL_PATH}")

    # 6. Visualizations (computed once, saved to static/)
    save_confusion_matrix(metrics["cm"],   os.path.join(STATIC_DIR, "confusion_matrix.png"))
    save_metrics_chart(metrics,            os.path.join(STATIC_DIR, "metrics.png"))
    save_feature_importance(rf_model, feature_names, os.path.join(STATIC_DIR, "feature_importance.png"))

    print("\n[DONE] Model training complete. Run: python app.py")


if __name__ == "__main__":
    main()
