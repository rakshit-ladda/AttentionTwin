"""
AttentionTwin Action-Aware Model Trainer
========================================
Trains a machine learning pipeline that explicitly conditions outcome prediction
on the candidate intervention action (allow, defer, suppress) alongside pre-decision features.
"""

import os
import json
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np
import joblib

from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.dummy import DummyClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    confusion_matrix,
)

from app.ml.feature_schema import (
    CATEGORICAL_FEATURE_NAMES,
    NUMERIC_FEATURE_NAMES,
    TARGET_BINARY,
)
from app.ml.feature_pipeline import validate_feature_dataset
from app.ml.split_utils import chronological_split

# Action-aware feature lists
ACTION_AWARE_CATEGORICAL_FEATURES: List[str] = CATEGORICAL_FEATURE_NAMES + ["proposed_action"]
ACTION_AWARE_NUMERIC_FEATURES: List[str] = NUMERIC_FEATURE_NAMES
ACTION_AWARE_ALL_FEATURES: List[str] = ACTION_AWARE_CATEGORICAL_FEATURES + ACTION_AWARE_NUMERIC_FEATURES


def build_action_aware_preprocessor() -> ColumnTransformer:
    """Preprocess numeric features with StandardScaler and categoricals (including action) with OneHotEncoder."""
    numeric_transformer = Pipeline(steps=[
        ("scaler", StandardScaler()),
    ])
    categorical_transformer = Pipeline(steps=[
        ("encoder", OneHotEncoder(handle_unknown="ignore", sparse_output=False)),
    ])

    return ColumnTransformer(
        transformers=[
            ("num", numeric_transformer, ACTION_AWARE_NUMERIC_FEATURES),
            ("cat", categorical_transformer, ACTION_AWARE_CATEGORICAL_FEATURES),
        ],
        remainder="drop",
    )


def compute_metrics(y_true: pd.Series, y_pred: np.ndarray, y_proba: Optional[np.ndarray] = None) -> Dict[str, Any]:
    """Calculate evaluation metrics for binary classification."""
    metrics: Dict[str, Any] = {
        "count": len(y_true),
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "precision": float(precision_score(y_true, y_pred, zero_division=0)),
        "recall": float(recall_score(y_true, y_pred, zero_division=0)),
        "f1": float(f1_score(y_true, y_pred, zero_division=0)),
        "confusion_matrix": confusion_matrix(y_true, y_pred).tolist(),
    }
    if y_proba is not None and len(np.unique(y_true)) > 1:
        try:
            metrics["roc_auc"] = float(roc_auc_score(y_true, y_proba))
        except Exception:
            metrics["roc_auc"] = None
    else:
        metrics["roc_auc"] = None
    return metrics


class ActionAwareModelTrainer:
    """Trains, evaluates, and serializes the action-conditioned prediction pipeline."""

    def __init__(self, artifacts_dir: str = "backend/artifacts"):
        self.artifacts_dir = artifacts_dir

    def train_and_save(
        self,
        dataset_path: str = "data/synthetic/feature_dataset.csv",
        selected_model: str = "random_forest",
    ) -> Dict[str, Any]:
        """
        Validate dataset, train action-conditioned classifiers, and save artifacts.
        """
        if not os.path.exists(dataset_path):
            raise FileNotFoundError(f"Feature dataset not found at: {dataset_path}")

        df = pd.read_csv(dataset_path)

        # Validate Phase 3 dataset
        val_summary = validate_feature_dataset(df)
        if not val_summary["is_valid"]:
            raise ValueError(f"Dataset validation failed: {val_summary['errors']}")

        # Map decision_action to proposed_action column
        df["proposed_action"] = df["decision_action"]

        # Chronological train/test split (80% train, 20% test per user)
        train_df, test_df, split_meta = chronological_split(df, train_ratio=0.8)

        X_train = train_df[ACTION_AWARE_ALL_FEATURES]
        y_train = train_df[TARGET_BINARY]
        X_test = test_df[ACTION_AWARE_ALL_FEATURES]
        y_test = test_df[TARGET_BINARY]

        # 1. Dummy Baseline
        dummy_pipe = Pipeline([
            ("preprocessor", build_action_aware_preprocessor()),
            ("classifier", DummyClassifier(strategy="most_frequent")),
        ])
        dummy_pipe.fit(X_train, y_train)
        dummy_preds = dummy_pipe.predict(X_test)
        dummy_metrics = compute_metrics(y_test, dummy_preds)

        # 2. Logistic Regression
        lr_pipe = Pipeline([
            ("preprocessor", build_action_aware_preprocessor()),
            ("classifier", LogisticRegression(max_iter=1000, random_state=42)),
        ])
        lr_pipe.fit(X_train, y_train)
        lr_preds = lr_pipe.predict(X_test)
        lr_proba = lr_pipe.predict_proba(X_test)[:, 1]
        lr_metrics = compute_metrics(y_test, lr_preds, lr_proba)

        # 3. Random Forest Classifier
        rf_pipe = Pipeline([
            ("preprocessor", build_action_aware_preprocessor()),
            ("classifier", RandomForestClassifier(n_estimators=100, max_depth=8, random_state=42)),
        ])
        rf_pipe.fit(X_train, y_train)
        rf_preds = rf_pipe.predict(X_test)
        rf_proba = rf_pipe.predict_proba(X_test)[:, 1]
        rf_metrics = compute_metrics(y_test, rf_preds, rf_proba)

        # Select model to serialize
        if selected_model == "logistic_regression":
            chosen_pipe = lr_pipe
            chosen_metrics = lr_metrics
            chosen_name = "LogisticRegression"
            chosen_preds = lr_preds
            chosen_proba = lr_proba
        else:
            chosen_pipe = rf_pipe
            chosen_metrics = rf_metrics
            chosen_name = "RandomForestClassifier"
            chosen_preds = rf_preds
            chosen_proba = rf_proba

        # Compute per-action breakdown metrics
        per_action_metrics = {}
        for action in ["allow", "defer", "suppress"]:
            mask = (test_df["proposed_action"] == action).values
            if np.sum(mask) > 0:
                y_sub_true = y_test.iloc[mask]
                y_sub_pred = chosen_preds[mask]
                y_sub_proba = chosen_proba[mask]
                per_action_metrics[action] = compute_metrics(y_sub_true, y_sub_pred, y_sub_proba)

        # Class distribution by action across dataset
        action_class_distribution = {}
        for action in ["allow", "defer", "suppress"]:
            sub = df[df["proposed_action"] == action]
            if len(sub) > 0:
                pos_rate = float(sub[TARGET_BINARY].mean())
                action_class_distribution[action] = {
                    "total_count": len(sub),
                    "positive_open_rate": round(pos_rate, 4),
                    "negative_rate": round(1.0 - pos_rate, 4),
                }

        # Save model artifact
        os.makedirs(self.artifacts_dir, exist_ok=True)
        model_path = os.path.join(self.artifacts_dir, "action_aware_model.joblib")
        joblib.dump(chosen_pipe, model_path)

        metadata = {
            "model_version": "action_aware_v1.0.0",
            "model_name": chosen_name,
            "target_variable": TARGET_BINARY,
            "target_definition": "1 if notification opened within 5 minutes, 0 if delayed or ignored",
            "data_provenance": "SYNTHETIC_DEVELOPMENT_DATA (CASCADE 2026 Simulation)",
            "disclaimer": (
                "This action-aware model was trained on synthetic simulation data to demonstrate counterfactual "
                "evaluation. It must not be interpreted as a proven causal effect or verified attention prediction."
            ),
            "feature_names": ACTION_AWARE_ALL_FEATURES,
            "categorical_features": ACTION_AWARE_CATEGORICAL_FEATURES,
            "numeric_features": ACTION_AWARE_NUMERIC_FEATURES,
            "num_training_rows": len(train_df),
            "num_test_rows": len(test_df),
            "split_metadata": split_meta,
            "overall_metrics": chosen_metrics,
            "per_action_metrics": per_action_metrics,
            "action_class_distribution": action_class_distribution,
            "comparison": {
                "dummy_baseline": dummy_metrics,
                "logistic_regression": lr_metrics,
                "random_forest": rf_metrics,
            },
            "trained_at": datetime.now(timezone.utc).isoformat(),
        }

        metadata_path = os.path.join(self.artifacts_dir, "action_aware_metadata.json")
        with open(metadata_path, "w") as f:
            json.dump(metadata, f, indent=2)

        return metadata
