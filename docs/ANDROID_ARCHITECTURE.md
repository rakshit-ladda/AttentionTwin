# Android architecture and verified limits

## Current implementation

The Android project at `frontend/android` is a Capacitor 8 WebView wrapper with Java `MainActivity`. It targets SDK 36 and has min SDK 24. `AttentionNotificationListener` is declared with `BIND_NOTIFICATION_LISTENER_SERVICE`; `AttentionListenerPlugin` reports access/connection status, reads/deletes local history, opens Android access settings, stores up to 12 daily local break times, and lets the user snooze an active event to the next configured time on API 26+. `NotificationAccessPanel` exposes this flow in the native app.

The local log uses a bounded 200-record `SharedPreferences` store with at most 32 transitions per record. It retains a SHA-256-derived event ID, source package, posted/updated/removed timestamps, lifecycle transition trail, clearability, removal reason, and expected snooze repost time; it does not persist title/body or Android's raw notification key. Event IDs deduplicate update/removal callbacks and permit an in-memory lookup for a user-triggered snooze. Android backup is disabled so this metadata is not included in app backup. This is a first metadata milestone, not a Room-backed general event schema. Break delivery uses Android system snoozing after a manual action; there is no automatic policy routing, exact-time guarantee, reboot receiver, or offline model inference.

The React app still queries the FastAPI health endpoint for its dashboard and counterfactual views. Native notification observation and snoozing are local, but predictions and the main dashboard need a configured backend URL. This APK is not yet an offline attention-management runtime.

## Public notification API boundary

An ordinary Android app can declare a `NotificationListenerService` protected by `android.permission.BIND_NOTIFICATION_LISTENER_SERVICE`, expose the service interface action, and ask the user to enable access in system Settings. The OS calls `onNotificationPosted` and `onNotificationRemoved` when notifications change. Treat the callbacks as post-publication observations. They do not provide a documented guarantee that a listener can inspect and block the initial banner, sound, or vibration before the user sees/hears it.

From API 26, a connected listener may call `snoozeNotification(key, durationMs)`. Android removes the snoozed item and posts it again when the snooze period expires. This provides a legitimate post-post snooze mechanism, but it is not an exact wall-clock break scheduler: doze, process/device state, OEM policies, user permission, and source-app behavior need validation. `NotificationAssistantService` and notification ranking/adjustment APIs are a distinct assistant/system role surface; do not assume ordinary listener access grants it.

For a first reliable implementation, prefer metadata-only local event logging, explicit permission status, and user-confirmed snooze. Do not globally edit other apps' notification channels. If automatic filtering is later added, offer an opt-in AttentionTwin-managed inbox and preserve clear recovery affordances. Important senders, calls, OTPs, and emergency/system alerts require explicit safe exceptions.

## Background and device limits

Listener reconnection, service callbacks, exact alarm policy, reboot recovery, notification access revocation, and Redmi/HyperOS battery management are not verified by unit tests. A real phone matrix must include app backgrounding, screen lock, process death, reboot, permission revocation, network-off/backend-off, and battery optimization. Do not assert physical behavior before running that checklist.

## Reference products checked

- **NotiFilter:** F-Droid listing is live and describes filters, dismiss/tap/delay/batch/mute actions, schedule, local history, and offline behavior. The listing identifies GPL-3.0-only. It is a mature public reference but its code/license is not being imported.
- **Android Digital Wellbeing Focus Mode:** Google's help/product materials describe pausing user-selected distracting apps with a break/temporary unpause. This is system wellbeing behavior, not an API that lets AttentionTwin directly inspect a personal focus session or automatically acquire the user's Focus Mode state.
- **Smart Notifications Organizer:** Google Play listing is live and markets notification prioritization using Usage Stats. Those are product claims; this audit did not verify implementation, source availability, or measured accuracy.
- **Nap (`io.leao.nap`):** the supplied Play URL did not resolve through the available search lookup, and no current first-party source or listing was verified. Do not rely on it as a maintained reference until checked directly in Play on a device/browser.

The existence of a reference app demonstrates a product pattern, not a guaranteed platform contract or evidence that its exact behavior works on HyperOS.

## Privacy requirements for native work

Default event record should contain only a generated local event ID, opaque notification key, package name, post/remove timestamps, safe category/channel metadata where present, and removal reason. Omit title/body, previews, people, and OTP content. Add retention and delete controls before collecting a long-term local history. Process locally; no upload by default.

## References

- [NotificationListenerService API](https://developer.android.com/reference/android/service/notification/NotificationListenerService)
- [NotificationListenerService Android guide](https://developer.android.com/develop/ui/views/notifications/notification-listener)
- [AlarmManager guide](https://developer.android.com/develop/background-work/services/alarms)
- [WorkManager guide](https://developer.android.com/develop/background-work/background-tasks/persistent)
- [NotiFilter F-Droid listing](https://f-droid.org/en/packages/co.adityarajput.notifilter/) — GPL-3.0-only listing describes local history, filtering, delay/snooze, scheduling, and offline use. Reference only; no code copied.
