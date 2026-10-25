# Privacy status and requirements

## Current implementation

The Android listener currently stores at most 200 metadata records in app-private `SharedPreferences`, with at most 32 transitions per record: generated hash ID, source package, timestamps, clearability, lifecycle state, and removal reason. It omits title/body, previews, contact identity, and raw system key; the app has a clear-history action. Android app backup is disabled. SharedPreferences is app-private storage but is not an encrypted database. The backend `NotificationEvent` SQLAlchemy model separately includes required `text` and can persist notification text when clients submit it. The React simulator/API path still calls the backend.

## Required defaults for native collection

- Ask for notification access with a clear explanation that it can reveal notification metadata from other apps.
- Store locally only a generated ID, opaque system key, package, timestamps, safe channel/category fields, and lifecycle state needed for history/scheduling.
- Do not persist title/body, message preview, OTP, contact identity, or sensitive notification extras by default.
- Do not upload notification data. Provide retention, history deletion, and profile deletion controls before building long-term collection.
- Record whether an outcome is observed, user-reported, proxy, synthetic, or predicted; avoid silently turning missing outcomes into negative labels.
- Keep explicit urgent sender/category exceptions on-device and ensure system/emergency alerts have safe handling.

Notification access is powerful. It does not grant permission to bypass app-specific security or guarantee notification interception before an alert. Users must be able to revoke access and still use the rest of the app.
