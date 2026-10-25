from fastapi import APIRouter, HTTPException, status
from app.schemas.counterfactual import (
    CounterfactualCompareRequest,
    CounterfactualCompareResponse,
)
from app.ml.counterfactual_engine import counterfactual_engine

router = APIRouter()


@router.post(
    "/counterfactuals/compare",
    response_model=CounterfactualCompareResponse,
    status_code=status.HTTP_200_OK,
    summary="Compare candidate notification actions for identical context",
)
def compare_counterfactual_actions(
    request: CounterfactualCompareRequest,
):
    """
    Simulate and compare outcomes under three candidate actions (allow, defer, suppress)
    for the exact same pre-decision notification arrival and user context.
    
    Guarantees:
    - Pre-decision context attributes are held strictly invariant.
    - Predictions are derived from the action-aware model.
    - Transparently discloses synthetic provenance and limitation boundaries.
    - Does NOT record hypothetical predictions into empirical observed outcome logs.
    """
    if not counterfactual_engine.is_ready:
        counterfactual_engine.load_model()

    if not counterfactual_engine.is_ready:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Action-aware model artifact is not loaded or has not been trained yet.",
        )

    return counterfactual_engine.compare_actions(request)
