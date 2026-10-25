"""
AttentionTwin Baseline Predictor Service
========================================
Loads the serialized model artifact from backend/artifacts/ and provides real-time
inference with strict validation, class probabilities, and transparent limitation disclaimers.
"""

import os
import json
from typing import Dict, Any, Optional
import pandas as pd
import joblib

from app.ml.feature_schema import (
    ALL_FEATURE_NAMES,
    COLD_START_DEFAULTS,
)
from app.schemas.ml import NotificationPredictionRequest, NotificationPredictionResponse, ModelStatusResponse


class PredictionService:
    """Service handling model artifact loading, verification, and inference."""

    def __init__(self, artifacts_dir: str = "backend/artifacts"):
        self.artifacts_dir = artifacts_dir
        self.model = None
        self.metadata = None
        self.load_model()

    def load_model(self) -> bool:
        """Attempt to load saved model and metadata from artifacts directory."""
        model_path = os.path.join(self.artifacts_dir, "baseline_model.joblib")
        metadata_path = os.path.join(self.artifacts_dir, "model_metadata.json")

        if os.path.exists(model_path) and os.path.exists(metadata_path):
            try:
                self.model = joblib.load(model_path)
                with open(metadata_path, "r") as f:
                    self.metadata = json.load(f)
                return True
            except Exception:
                self.model = None
                self.metadata = None
                return False
        return False

    @property
    def is_ready(self) -> bool:
        return self.model is not None and self.metadata is not None

    def get_status(self) -> ModelStatusResponse:
        """Return model metadata, operational status, and synthetic provenance."""
        if not self.is_ready:
            return ModelStatusResponse(
                is_model_loaded=False,
                data_provenance="NO_MODEL_LOADED",
            )

        return ModelStatusResponse(
            is_model_loaded=True,
            model_name=self.metadata.get("model_name"),
            model_version=self.metadata.get("model_version"),
            target=self.metadata.get("target_variable"),
            data_provenance=self.metadata.get("data_provenance", "SYNTHETIC_DEVELOPMENT_DATA"),
            features_count=len(self.metadata.get("feature_names", [])),
            metrics=self.metadata.get("metrics"),
            trained_at=self.metadata.get("trained_at"),
        )

    def predict(self, request: NotificationPredictionRequest) -> NotificationPredictionResponse:
        """
        Run inference on a single validated notification feature payload.
        """
        if not self.is_ready:
            raise RuntimeError("Model artifact is not loaded or has not been trained yet.")

        # Convert request to dictionary
        data_dict = request.model_dump()

        # Fill any missing numeric features with cold-start defaults
        for feat in ALL_FEATURE_NAMES:
            if feat not in data_dict or data_dict[feat] is None:
                data_dict[feat] = COLD_START_DEFAULTS.get(feat, 0.0)

        # Build single-row DataFrame with required feature column ordering
        row_df = pd.DataFrame([data_dict])[ALL_FEATURE_NAMES]

        # Predict class and probability
        pred_class = int(self.model.predict(row_df)[0])
        prob_opened = float(self.model.predict_proba(row_df)[0][1])

        label = "opened_within_5min" if pred_class == 1 else "not_opened_quickly"

        return NotificationPredictionResponse(
            predicted_class=pred_class,
            predicted_label=label,
            probability_opened_quickly=round(prob_opened, 4),
            model_version=self.metadata.get("model_version", "baseline_v1.0.0"),
            data_provenance=self.metadata.get("data_provenance", "SYNTHETIC_DEVELOPMENT_DATA"),
            evaluation_basis=self.metadata.get("split_metadata", {}).get("strategy", "chronological_split"),
            limitations_disclaimer=(
                "Prediction is based on synthetic development data simulation heuristics. "
                "It does not represent verified human cognitive state, focus impairment, or real attention distraction."
            ),
        )


# Global singleton instance
predictor_service = PredictionService()
