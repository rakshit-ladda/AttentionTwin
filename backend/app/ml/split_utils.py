"""
AttentionTwin Train/Test Split Utilities
=======================================
Implements leakage-aware dataset splitting strategies for ML evaluation.

Strategies:
1. CHRONOLOGICAL SPLIT (Temporal Generalization):
   Trains on earlier events and tests on subsequent future events.
   Measures the model's ability to forecast future user reactions without lookahead leakage.

2. USER-HELD-OUT SPLIT (Cross-User / Population Generalization):
   Trains on a cohort of users and tests entirely on unobserved users.
   Measures zero-shot cold-start performance for newly onboarded individuals.
"""

from typing import Tuple, List, Dict, Any
import pandas as pd
import numpy as np


def chronological_split(
    df: pd.DataFrame,
    train_ratio: float = 0.8,
) -> Tuple[pd.DataFrame, pd.DataFrame, Dict[str, Any]]:
    """
    Split the dataset chronologically per user or globally.
    Prevents temporal lookahead leakage.
    """
    df_sorted = df.sort_values("timestamp").reset_index(drop=True)
    
    # Split chronologically per user to balance representation
    train_indices = []
    test_indices = []

    for user_id, group in df_sorted.groupby("user_id"):
        n = len(group)
        split_point = int(n * train_ratio)
        train_indices.extend(group.index[:split_point])
        test_indices.extend(group.index[split_point:])

    train_df = df_sorted.loc[train_indices].sort_values("timestamp").reset_index(drop=True)
    test_df = df_sorted.loc[test_indices].sort_values("timestamp").reset_index(drop=True)

    metadata = {
        "strategy": "chronological_split",
        "train_ratio": train_ratio,
        "train_rows": len(train_df),
        "test_rows": len(test_df),
        "train_time_range": [str(train_df["timestamp"].min()), str(train_df["timestamp"].max())],
        "test_time_range": [str(test_df["timestamp"].min()), str(test_df["timestamp"].max())],
        "description": "Splits each user's event timeline into 80% past history for training and 20% future events for evaluation.",
    }

    return train_df, test_df, metadata


def user_held_out_split(
    df: pd.DataFrame,
    test_users_count: int = 2,
    seed: int = 42,
) -> Tuple[pd.DataFrame, pd.DataFrame, Dict[str, Any]]:
    """
    Hold out entire users from the training set.
    Evaluates cross-user generalization and cold-start robustness.
    """
    users = np.array(sorted(df["user_id"].unique()))
    rng = np.random.RandomState(seed)
    shuffled_users = rng.permutation(users)

    test_users = set(shuffled_users[:test_users_count])
    train_users = set(shuffled_users[test_users_count:])

    train_df = df[df["user_id"].isin(train_users)].sort_values("timestamp").reset_index(drop=True)
    test_df = df[df["user_id"].isin(test_users)].sort_values("timestamp").reset_index(drop=True)

    metadata = {
        "strategy": "user_held_out_split",
        "train_users": sorted(list(train_users)),
        "test_users": sorted(list(test_users)),
        "train_rows": len(train_df),
        "test_rows": len(test_df),
        "description": "Holds out entire synthetic users to evaluate cold-start population generalization.",
    }

    return train_df, test_df, metadata
