# Problem statement compliance audit

Audit baseline: commit `107fb98`, checked 2026-10-26. “Implemented” means evidenced by current code, not implied by the README. No physical device has been tested in this audit.

| Requirement | Status | Evidence and limitation |
|---|---|---|
| Learn when this user focuses best | Not implemented | `data/synthetic/feature_dataset.csv` has simulated focus labels/context, but no personal focus-session or task-completion data. `frontend/src/components/AttentionProfile.tsx` is dashboard/profile UI, not a native personal learner. |
| Learn causes of interruption and app fragmentation | Not implemented | No UsageStats/Accessibility/foreground-app observation or real focus-session outcome pipeline exists in the manifest/native code. Synthetic associations cannot establish causation. |
| Learn content types that cause prolonged sessions | Simulated only | Raw generator writes simulated duration values, but the 8,000-row model feature CSV omits them and contains only opening/outcome labels. No message content is needed or stored natively. |
| Learn which notifications matter | Not implemented | Opening probability and app/category heuristics are not importance labels. No urgent-sender preferences or user feedback decision policy is connected to real notifications. |
| Estimate fatigue | Not implemented | No longitudinal app/session/break observation or fatigue self-report exists. |
| Compare ALLOW / DEFER / SUPPRESS | Partial, synthetic/rule-based | The optional backend `backend/app/ml/counterfactual_engine.py::CounterfactualEngine.compare_actions` evaluates a synthetic opening classifier and fixed duration rules. Android offline mode uses conservative rules and reports personal probabilities/durations as unavailable. Neither is causal estimation. |
| Use context-aware decision policy | Simulated API only | `counterfactual_engine.py` returns a heuristic recommendation. No Android notification reaches this policy, and recommendations are not executed on-device. |
| Background Android notification detection | Partially implemented; build/device verification pending | `AttentionNotificationListener.java` declares posted/removed callbacks and keeps a bounded metadata-only `SharedPreferences` log. The user can grant access through `AttentionListenerPlugin` and inspect local events in `NotificationAccessPanel`. Java sources compile via `javac`; Gradle/APK packaging and OS callback behavior have not been verified. |
| Prevent original first banner/sound/vibration | Technically unavailable as a guarantee to ordinary listener apps | Listener callbacks concern posted notifications; public snooze is API 26+ and acts after user/UI decision. Do not promise pre-display interception. System/OEM behavior requires testing. |
| Defer/release at configured breaks | Partially implemented | The user can configure up to 12 daily break times and manually snooze an active event to the next time through Android's public snooze API on API 26+. A repost should be observed and logged. This is user-triggered, relies on Android's timing, and has no physical-device verification or reboot guarantee. Current API's `+25m` remains a display estimate, not scheduling. |
| Keep notification history recoverable | Partially implemented locally | A bounded 200-event log tracks hashed stable event ID, source package, timestamps, lifecycle/removal reason and clearability. It omits content and supports deletion. A snoozed notification is managed by Android and reposts on expiry; AttentionTwin has not built a separate recovery inbox. |
| Run without laptop/network | Partially implemented | Android defaults to `frontend/src/native/offlineRuntime.ts` for comparison guidance, manually saved metadata-only event history, profile status, and local health status. State is stored in WebView local storage. This runtime has no personal ML model, and does not run the Python backend/database or automatically decide notification actions. Native notification metadata and break snooze are separately local. |
| Personalize from real observations | Not implemented | Existing training data is synthetic; no native event/outcome learning pipeline exists. |
| Automated verification | Partial | Backend suite previously passed 39 tests. Frontend production build and Gradle debug APK packaging passed after the offline runtime change. No Android OS callback or physical-device behavior is verified. |
| Installable APK | Built, installation blocked by Play Protect on user's phone | `frontend/android/app/build/outputs/apk/debug/AttentionTwin-offline-debug.apk` is the offline-capable debug APK signed with the existing Windows debug key. User's screenshot shows Play Protect blocks this sideloaded build because it requests sensitive notification access. |

## Data and model target inventory

| Source | Verified content | Supports | Does not support |
|---|---|---|---|
| `data/synthetic/feature_dataset.csv` | 8,000 synthetic rows; 10 synthetic users; 23 columns | Simulated `opened_within_5min`, `outcome_label`, synthetic action/context; chronological/user split experiments | Human generalization, observed duration, measured resumption, causal outcomes |
| `data/synthetic/raw_synthetic_events.json` | Generated event records; inspect the checked-in JSON before use | Simulated latency, browsing duration, task-resumption duration | Human outcomes; the generator's own synthetic labels are not empirical evidence |
| AmI-2018 | 176,195 notification records, 14 users; post/remove times, package, alert/device state; GPL-3.0 repo | Response/removal timing proxies and context, subject to target semantics and license | App browsing duration, resumption, intervention alternatives, content types, current-user personalization |
| AmI-2019 | 229,792 notification records, 44 users; notification/device/venue context | Notification handling and context analyses | Direct task-resumption/browsing labels and linked identity across datasets |
| UbiqLog | General smartphone lifelog/app-use observations; source code BSD-2-Clause; historical dataset has privacy restriction | Potential app-use timing/context after schema and access review | Notification-level response labels unless the exact release proves them |

Public data candidates must be downloaded and inspected before training. Keep observed, user-reported, proxy, and synthetic labels separate. Do not merge participant IDs between unrelated datasets.
