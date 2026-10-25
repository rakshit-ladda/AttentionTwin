from fastapi import APIRouter, HTTPException, status
from app.schemas.ml import (
    NotificationPredictionRequest,
    NotificationPredictionResponse,
    ModelStatusResponse,
)
from app.ml.predictor import predictor_service

router = APIRouter()


@router.get(
    "/models/status",
    response_model=ModelStatusResponse,
    status_code=status.HTTP_200_OK,
    summary="Get baseline model status and metadata",
)
def get_model_status():
    """Retrieve operational status, metadata, evaluation basis, and provenance of the ML model."""
    # Attempt to reload if not ready
    if not predictor_service.is_ready:
        predictor_service.load_model()
    return predictor_service.get_status()


@router.post(
    "/models/predict",
    response_model=NotificationPredictionResponse,
    status_code=status.HTTP_200_OK,
    summary="Predict notification outcome from arrival features",
)
def predict_notification_outcome(
    request: NotificationPredictionRequest,
):
    """
    Predict whether a notification will be opened within 5 minutes given arrival-time features.
    Transparently reports class probabilities, data provenance, and limitation disclaimers.
    """
    if not predictor_service.is_ready:
        predictor_service.load_model()

    if not predictor_service.is_ready:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Baseline ML model artifact is not loaded or has not been trained yet.",
        )

    return predictor_service.predict(request)
