# AttentionTwin Synthetic Development Dataset

> **DISCLAIMER:**  
> **SYNTHETIC DEVELOPMENT DATA — NOT REAL USER DATA**  
> All records, user profiles, and simulated behaviors in this directory were deterministically generated using synthetic simulation assumptions. They are intended solely to develop, test, and validate data ingestion pipelines and baseline machine learning estimators without claiming real human psychological validity.

---

## Dataset Summary

- **Total Events:** 8,000
- **Total Synthetic Users:** 10 (`user_001` through `user_010`)
- **Time Horizon:** 14 simulated days (Oct 1, 2026 – Oct 15, 2026)
- **Random Seed:** 42 (deterministic reproduction)
- **Generator Version:** `1.0.0`
- **Binary Target Distribution (`opened_within_5min`):**
  - Class `0` (Not opened quickly / deferred / ignored): 65.3% (5,226 events)
  - Class `1` (Opened within 5 minutes): 34.7% (2,774 events)
- **Multiclass Distribution (`outcome_label`):**
  - `opened_later`: 35.2% (2,812 events)
  - `opened_quickly`: 34.7% (2,774 events)
  - `ignored`: 30.2% (2,414 events)

---

## Column Data Dictionary (`feature_dataset.csv`)

### 1. Metadata Identifiers
- `event_id`: Unique integer event identifier (1 – 8000).
- `user_id`: Synthetic user identifier string (`user_001` – `user_010`).
- `timestamp`: ISO-8601 UTC timestamp of notification arrival.
- `decision_action`: Intervention action simulated (`allow`, `defer`, `suppress`).

### 2. Notification Features (Available at Arrival)
- `source_app`: Originating application (`Slack`, `Gmail`, `WhatsApp`, `GitHub`, `Calendar`, `Twitter`, `Instagram`, `Datadog`, `Amazon`, `UberEats`).
- `app_category`: Domain category (`communication`, `work`, `productivity`, `social`, `system_alert`, `marketing`).
- `notification_category`: Specific notification subtype (e.g. `direct_message`, `meeting_reminder`, `cpu_spike`).
- `text_length`: Character length of notification text preview (10–250 chars).
- `hour_of_day`: Arrival hour in 24-hour format (0–23).
- `day_of_week`: Day of week (0 = Monday, 6 = Sunday).
- `is_weekend`: Binary flag (1 if Saturday or Sunday, else 0).

### 3. Context Features
- `focus_mode`: User cognitive state (`deep_work`, `meeting`, `casual_browsing`, `off_hours`).
- `is_focus_session`: Binary flag indicating whether timed focus mode is active (1 or 0).
- `recent_notification_count_15m`: Volume of alerts received in trailing 15 minutes.
- `minutes_since_last_notification`: Time in minutes since immediately preceding alert (capped at 1440).
- `notification_load_1h`: Trailing 60-minute notification volume.

### 4. Historical Behavioral Features (Computed on strictly prior events)
- `app_historical_open_rate`: Proportion of prior notifications from this app opened quickly (<5 min).
- `app_historical_ignore_rate`: Proportion of prior notifications from this app dismissed or ignored.
- `user_historical_open_rate`: Global historical quick-open rate for this user across all apps prior to this event.
- `recent_allow_rate_1h`: Fraction of interventions in the past hour where the alert was allowed.
- `recent_suppress_rate_1h`: Fraction of interventions in the past hour where alerts were suppressed.

### 5. Target Outcomes (Supervised Learning Labels)
- `opened_within_5min`: Binary label for classification (1 = opened quickly within 5 minutes, 0 = delayed or ignored).
- `outcome_label`: Multiclass outcome category (`opened_quickly`, `opened_later`, `ignored`).

---

## Cold-Start Handling Strategy

For initial events when a user or app has zero prior historical events, the pipeline applies neutral uninformative baseline priors:
- `user_historical_open_rate`: `0.5`
- `app_historical_open_rate`: `0.5`
- `app_historical_ignore_rate`: `0.3`
- `recent_allow_rate_1h`: `0.5`
- `recent_suppress_rate_1h`: `0.2`
- `minutes_since_last_notification`: `120.0` minutes
- `recent_notification_count_15m`: `0`
- `notification_load_1h`: `0`

---

## Leakage Protections Enforced

1. **Chronological Calculation:** Historical rate and rolling window counts are evaluated using strictly prior events ($t_{prior} < t_{event}$).
2. **Zero Outcome Leakage:** No observation, latency, or outcome label is used as an input feature.
3. **Latent Isolation:** Simulation-only parameters (`user_responsiveness_trait`, `true_latent_urgency`) are excluded from `feature_dataset.csv`.
4. **Categorical Semantic Integrity:** Categorical columns remain textual representations and are not arbitrarily mapped to integer ranks.

---

## External Dataset Research Boundary (Phase 3 Requirement 10)

Future versions may integrate real-world empirical notification interaction datasets. However, generic smartphone screen-time datasets (e.g. daily unlock counts, total app usage time) are **not** suitable for AttentionTwin because they lack granular notification-level interaction telemetry.

A suitable real-world external dataset must satisfy:
1. **Notification-Level Granularity:** Per-notification arrival timestamps and application identifiers.
2. **Arrival Context:** Device state at notification arrival (screen on/off, foreground app, active focus/DND state).
3. **Observed User Interaction:** Exact response timestamp, click/dismiss action, or response latency.
4. **Intervention Feasibility:** Logging of whether the alert was displayed immediately or suppressed by OS notification policy.
