# Privacy status and requirements

## Current implementation

The Android shell currently has no notification listener or local notification store. The backend `NotificationEvent` SQLAlchemy model includes a required `text` field and can persist notification text when clients submit it. The React simulator/API path is not an on-device private notification pipeline. The backend SQLite database is ignored by Git, but local persistence is not encryption or a deletion policy by itself.

## Required defaults for native collection

- Ask for notification access with a clear explanation that it can reveal notification metadata from other apps.
- Store locally only a generated ID, opaque system key, package, timestamps, safe channel/category fields, and lifecycle state needed for history/scheduling.
- Do not persist title/body, message preview, OTP, contact identity, or sensitive notification extras by default.
- Do not upload notification data. Provide retention, history deletion, and profile deletion controls before building long-term collection.
- Record whether an outcome is observed, user-reported, proxy, synthetic, or predicted; avoid silently turning missing outcomes into negative labels.
- Keep explicit urgent sender/category exceptions on-device and ensure system/emergency alerts have safe handling.

Notification access is powerful. It does not grant permission to bypass app-specific security or guarantee notification interception before an alert. Users must be able to revoke access and still use the rest of the app.
