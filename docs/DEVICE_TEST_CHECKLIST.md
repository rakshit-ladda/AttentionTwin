# Physical-device checklist

Status: all cases below remain **not run** in this audit. There is no recorded Redmi Note 13 Pro / HyperOS test evidence. Automated API tests cannot establish Android notification callback or OEM behavior.

For each run, record device model, Android/HyperOS build, app version/commit, permission state, battery settings, exact steps, timestamp, evidence, expected/actual behavior, and pass/fail. Use test notifications without private content.

| Scenario | Expected behavior to verify | Status |
|---|---|---|
| Social notification during deep work | Listener receives metadata; first alert behavior is observed and documented; no content is persisted by default | Not run |
| Important email / urgent sender | User exception wins over low open probability | Not run |
| Marketing notification | User-selected policy and recovery behavior are honored | Not run |
| Notification during break | Configured break policy is used | Not run |
| Defer to break | Snooze/release occurs once and remains recoverable | Not run |
| Suppressed/dismissed item | History/recovery is available where supported | Not run |
| User overrides | Override persists and affects subsequent policy | Not run |
| Access revoked | UI reports missing access and app fails safely | Not run |
| App backgrounded / screen locked | Listener and local scheduler behavior are observed | Not run |
| Network and laptop unavailable | Local decisions/history continue without backend | Not run |
| Process death / reboot | Listener reconnects, alarms/work recover, no duplicate delivery | Not run |
| Unsupported/incomplete notification | Metadata extraction fails safely without crashing | Not run |
| Low model confidence / inference error | Conservative fallback and explanation are shown | Not run |
| Notification updated or removed | Lifecycle events deduplicate and retain correct state | Not run |
| Permission and battery restrictions | Settings/OEM effects are explained; no false reliability claim | Not run |
| History across app restart | Local records and deletion behave as specified | Not run |
