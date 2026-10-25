"""
AttentionTwin Baseline ML Trainer
================================
Trains and evaluates baseline classifiers on the Phase 3 feature dataset.
Includes Dummy baseline comparison, leakage-aware splitting, ColumnTransformer preprocessing,
and safe artifact serialization.
"""

import os
import json
from datetime import datetime, timezone
from typing import Dict, Any, Tuple, Optional
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
    ALL_FEATURE_NAMES,
    CATEGORICAL_FEATURE_NAMES,
    NUMERIC_FEATURE_NAMES,
    TARGET_BINARY,
)
from app.ml.feature_pipeline import validate_feature_dataset
from app.ml.split_utils import chronological_split, user_held_out_split


def build_preprocessor() -> ColumnTransformer:
    """Build a ColumnTransformer that scales numerics and one-hot encodes categoricals."""
    numeric_transformer = Pipeline(steps=[
        ("scaler", StandardScaler()),
    ])
    categorical_transformer = Pipeline(steps=[
        ("encoder", OneHotEncoder(handle_unknown="ignore", sparse_output=False)),
    ])

    return ColumnTransformer(
        transformers=[
            ("num", numeric_transformer, NUMERIC_FEATURE_NAMES),
            ("cat", categorical_transformer, CATEGORICAL_FEATURE_NAMES),
        ],
        remainder="drop",
    )


def evaluate_pipeline(
    model_pipeline: Any,
    X_train: pd.DataFrame,
    y_train: pd.Series,
    X_test: pd.DataFrame,
    y_test: pd.Series,
) -> Dict[str, Any]:
    """Train pipeline and calculate standard classification metrics."""
    model_pipeline.fit(X_train, y_train)
    y_pred = model_pipeline.predict(X_test)

    # Class probabilities if supported
    y_proba = None
    roc_auc = None
    if hasattr(model_pipeline, "predict_proba"):
        try:
            y_proba = model_pipeline.predict_proba(X_test)[:, 1]
            roc_auc = float(roc_auc_score(y_test, y_proba))
        except Exception:
            pass

    cm = confusion_matrix(y_test, y_pred).tolist()

    return {
        "accuracy": float(accuracy_score(y_test, y_pred)),
        "precision": float(precision_score(y_test, y_pred, zero_division=0)),
        "recall": float(recall_score(y_test, y_pred, zero_division=0)),
        "f1": float(f1_score(y_test, y_pred, zero_division=0)),
        "roc_auc": roc_auc,
        "confusion_matrix": cm,
    }


class BaselineModelTrainer:
    """Orchestrates validation, splitting, training, evaluation, and artifact saving."""

    def __init__(self, artifacts_dir: str = "backend/artifacts"):
        self.artifacts_dir = artifacts_dir

    def train_and_save(
        self,
        dataset_path: str = "data/synthetic/feature_dataset.csv",
        split_strategy: str = "chronological",
        selected_model: str = "random_forest",
    ) -> Dict[str, Any]:
        """
        Validate dataset, train baseline models, and save artifacts.
        """
        if not os.path.exists(dataset_path):
            raise FileNotFoundError(f"Feature dataset not found at: {dataset_path}")

        df = pd.read_csv(dataset_path)

        # Validate Phase 3 dataset
        val_summary = validate_feature_dataset(df)
        if not val_summary["is_valid"]:
            raise ValueError(f"Dataset validation failed: {val_summary['errors']}")

        # Split data
        if split_strategy == "chronological":
            train_df, test_df, split_meta = chronological_split(df, train_ratio=0.8)
        else:
            train_df, test_df, split_meta = user_held_out_split(df, test_users_count=2, seed=42)

        X_train = train_df[ALL_FEATURE_NAMES]
        y_train = train_df[TARGET_BINARY]
        X_test = test_df[ALL_FEATURE_NAMES]
        y_test = test_df[TARGET_BINARY]

        # 1. Dummy Classifier Baseline
        dummy_pipe = Pipeline([
            ("preprocessor", build_preprocessor()),
            ("classifier", DummyClassifier(strategy="most_frequent")),
        ])
        dummy_metrics = evaluate_pipeline(dummy_pipe, X_train, y_train, X_test, y_test)

        # 2. Logistic Regression
        lr_pipe = Pipeline([
            ("preprocessor", build_preprocessor()),
            ("classifier", LogisticRegression(max_iter=1000, random_state=42)),
        ])
        lr_metrics = evaluate_pipeline(lr_pipe, X_train, y_train, X_test, y_test)

        # 3. Random Forest Classifier
        rf_pipe = Pipeline([
            ("preprocessor", build_preprocessor()),
            ("classifier", RandomForestClassifier(n_estimators=100, max_depth=8, random_state=42)),
        ])
        rf_metrics = evaluate_pipeline(rf_pipe, X_train, y_train, X_test, y_test)

        # Choose model artifact to serialize
        if selected_model == "logistic_regression":
            chosen_pipeline = lr_pipe
            chosen_metrics = lr_metrics
            chosen_name = "LogisticRegression"
        else:
            chosen_pipeline = rf_pipe
            chosen_metrics = rf_metrics
            chosen_name = "RandomForestClassifier"

        # Ensure artifact directory exists
        os.makedirs(self.artifacts_dir, exist_ok=True)
        model_artifact_path = os.path.join(self.artifacts_dir, "baseline_model.joblib")
        joblib.dump(chosen_pipeline, model_artifact_path)

        # Build and save metadata
        metadata = {
            "model_version": "baseline_v1.0.0",
            "model_name": chosen_name,
            "target_variable": TARGET_BINARY,
            "target_definition": "1 if notification was opened within 5 minutes, 0 if delayed or ignored",
            "data_provenance": "SYNTHETIC_DEVELOPMENT_DATA (CASCADE 2026 Simulation)",
            "disclaimer": (
                "This model was trained exclusively on synthetic development data. "
                "Performance metrics reflect simulation heuristics and do not establish "
                "real-world human attention predictability."
            ),
            "training_dataset_source": dataset_path,
            "num_training_rows": len(train_df),
            "num_test_rows": len(test_df),
            "feature_names": ALL_FEATURE_NAMES,
            "categorical_features": CATEGORICAL_FEATURE_NAMES,
            "numeric_features": NUMERIC_FEATURE_NAMES,
            "split_metadata": split_meta,
            "trained_at": datetime.now(timezone.utc).isoformat(),
            "metrics": chosen_metrics,
            "comparison": {
                "dummy_baseline": dummy_metrics,
                "logistic_regression": lr_metrics,
                "random_forest": rf_metrics,
            },
        }

        metadata_path = os.path.join(self.artifacts_dir, "model_metadata.json")
        with open(metadata_path, "w") as f:
            json.dump(metadata, f, indent=2)

        return metadata
