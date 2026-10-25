# Counterfactual design status

## Current API semantics

`POST /api/counterfactuals/compare` creates three input rows with the same submitted pre-notification fields and varies only `proposed_action`. The trained action-aware classifier outputs a synthetic-data probability for `opened_within_5min`. `backend/app/ml/counterfactual_engine.py` then assigns browsing and resumption values from fixed dictionaries, sets a fixed 25-minute defer interval, and applies a hard-coded recommendation policy.

These are exploratory synthetic scenario outputs. They are not measured effects of the actions. The generated training data selects actions using heuristics, so the action-conditioned classifier has policy-selection bias. The unchosen alternatives have no observed labels. Current interruption values assume an immediate open probability multiplied by category/focus constants; the result is neither a learned duration distribution nor calibrated causal outcome.

## Intended action contract

- **ALLOW:** leave the original app notification untouched. The listener cannot guarantee interception before the initial alert.
- **DEFER:** use public snooze only after a user-selected defer action and only when notification access is granted and the notification is still active. API 26+ documents snooze and repost callbacks. Actual break-time precision and OEM behavior need device verification.
- **SUPPRESS:** ordinary listener-based removal happens after posting and can dismiss only clearable notifications. Preserve local metadata/recovery entry and do not claim the initial alert was prevented. Avoid silently changing global channels or DND.

## Decision policy needed

Separate predicted response from importance. Preserve explicit user-configured urgent sender/category exceptions. Compare expected interruption burden against the value and risk of missing/delaying the item, scheduled break time, and model uncertainty. When importance is unknown or uncertainty is high, favor allow or ask for user policy rather than automatic suppression. Offer override and persist the action actually taken.

## Evidence needed to improve estimates

Log the chosen action and observable downstream behavior locally. Use actual session intervals and return-to-focus events only with permissions and clear consent. User reports must be marked as such. Randomized comparisons require ethical review/consent and safe exceptions; observational correlations must not be described causally. Until these signals exist, expose duration numbers only as labeled synthetic or rule-based scenario illustrations, with uncertainty rather than false precision.
